"""Research implementation; see README.md for source conventions and limits."""
import math
import numpy as np
import pandas as pd

VERSION = "source-contracts/1"

LPPLS_SPANS=list(range(750,49,-5))
LPPLS_CONVENTIONS={
    'source':'Shu and Zhu arxiv:1905.09640 sections 2.2–2.3; Filimonov/Sornette arxiv:1108.0099 eqs13–17',
    'windows':'141 spans750..50 step5, dt=t2-t1 in trading sessions; both endpoints included (751..51 observations)',
    'solver':'CMA-ES; normalized coordinates; population16; sigma.2; maxiter2000; deterministic seed137+span',
    'confidence':'qualified windows / all141 windows; positive and negative signs separate',
    'oscillations':'omega/pi * log((tc-t1)/(tc-t2)); follows half-period prose, conflicts with printed omega/2 equation',
    'lomb':'Astropy floating-mean LombScargle; angular frequencies1..50;5 samples/peak; Baluev false-alarm approximation',
    'unit_root':'arch ADF constant/AIC automatic lag, PP constant with floor(12*(n/100)^.25) lags; significance.10',
    'unresolved':'paper omits solver settings, Lomb grid/FAP method and unit-root lag/trend; oscillation equation contradicts prose',
    'empirical_replication':'NVDA is a new-universe application, not Chinese-index result reproduction',
}


def lppls_linear(t,log_prices,tc,m,omega):
    t=np.asarray(t,float);y=np.asarray(log_prices,float);d=tc-t
    if t.ndim!=1 or len(t)<4 or y.shape!=t.shape or not np.isfinite(t).all() or not np.isfinite(y).all() or not np.isfinite([tc,m,omega]).all() or (d<=0).any():
        raise ValueError('finite aligned observations before critical time required')
    f=d**m;phase=omega*np.log(d)
    design=np.column_stack([np.ones(len(t)),f,f*np.cos(phase),f*np.sin(phase)])
    coefficients,_,rank,_=np.linalg.lstsq(design,y,rcond=None)
    if rank<4:raise ValueError('singular LPPLS design')
    prediction=design@coefficients
    return coefficients,prediction,float(np.square(prediction-y).sum())


def lppls_qualified(row,t1,t2):
    return bool(.01<=row['m']<=.99 and 2<=row['omega']<=25 and t2<row['tc']<=t2+(t2-t1)/5
                and row['damping']>=1 and row['oscillations']>=2.5 and row['relative_error']<=.15
                and all(np.isfinite(row[k]) and row[k]<=.1 for k in ('lomb_p','adf_p','pp_p')))


def lppls_confidence(rows):
    if not rows or not all(row['complete'] for row in rows):return {'positive':None,'negative':None}
    return {sign:sum(bool(r['qualified_'+sign]) for r in rows)/len(rows) for sign in ('positive','negative')}


def lppls_window(prices,seed=137):
    import cma
    from arch.unitroot import ADF,PhillipsPerron
    from astropy.timeseries import LombScargle
    y=np.log(np.asarray(prices,float));t=np.arange(len(y),dtype=float);span=t[-1]
    if len(y)<51 or not np.isfinite(y).all() or np.ptp(y)<1e-12:raise ValueError('insufficient or constant LPPLS observations')
    def decode(q):return span+q[0]*span/3,q[1],1+49*q[2]
    def objective(q):
        tc,m,w=decode(q)
        try:
            coefficients,_,error=lppls_linear(t,y,tc,m,w)
            _,b,c1,c2=coefficients;c=np.hypot(c1,c2);damping=m*abs(b)/(w*c) if c>0 else np.inf
            return error if damping>=1 else 1e6+(1-damping)*1e6+error
        except (ValueError,np.linalg.LinAlgError):return 1e12
    es=cma.CMAEvolutionStrategy([.3,.5,.2],.2,{'bounds':[[1e-8,1e-8,0.],[1.,1.,1.]],'popsize':16,
         'maxiter':2000,'seed':seed,'verbose':-9,'verb_log':0,'tolfun':1e-10,'tolx':1e-10})
    while not es.stop():
        candidates=es.ask();es.tell(candidates,[objective(q) for q in candidates])
    row={'span':int(span),'complete':'maxiter' not in es.stop(),'qualified_positive':False,'qualified_negative':False,
         'evaluations':int(es.result.evaluations),'stop':{str(k):str(v) for k,v in es.stop().items()}}
    if not row['complete']:return row
    tc,m,w=decode(es.result.xbest);coefficients,prediction,error=lppls_linear(t,y,tc,m,w)
    a,b,c1,c2=coefficients;c=np.hypot(c1,c2)
    damping=m*abs(b)/(w*c) if c>0 else np.inf
    if not np.isfinite(damping):raise ValueError('undefined LPPLS damping')
    row.update(tc=float(tc),m=float(m),omega=float(w),a=float(a),b=float(b),c1=float(c1),c2=float(c2),
               damping=float(damping),oscillations=float(w/np.pi*np.log(tc/(tc-span))),
               relative_error=float(np.max(np.abs(np.expm1(prediction-y)))),squared_error=error)
    residual=prediction-y;d=tc-t;detrended=(y-a-b*d**m)/d**m
    lomb=LombScargle(np.log(d),detrended,fit_mean=True,center_data=True,normalization='standard')
    minimum=1/(2*np.pi);maximum=50/(2*np.pi)
    _,power=lomb.autopower(minimum_frequency=minimum,maximum_frequency=maximum,samples_per_peak=5)
    lomb_p=lomb.false_alarm_probability(float(np.max(power)),method='baluev',minimum_frequency=minimum,maximum_frequency=maximum,samples_per_peak=5)
    lags=int(np.floor(12*(len(y)/100)**.25))
    row.update(lomb_p=float(lomb_p),adf_p=float(ADF(residual,trend='c',method='aic',max_lags=lags).pvalue),
               pp_p=float(PhillipsPerron(residual,lags=lags,trend='c').pvalue))
    if not all(np.isfinite(row[k]) for k in ('tc','m','omega','a','b','c1','c2','damping','oscillations','relative_error','squared_error','lomb_p','adf_p','pp_p')):
        raise ValueError('nonfinite LPPLS fit or diagnostic')
    qualified=lppls_qualified(row,0.,span)
    row.update(qualified_positive=bool(qualified and b<0),qualified_negative=bool(qualified and b>0))
    return row


def fit_lppls(close,seed=137):
    from ._inputs import close_values
    from arch.utility.exceptions import InfeasibleTestException
    close=close_values(close)
    if len(close)<751:raise ValueError('LPPLS paper recipe requires 751 observations for span750')
    rows=[]
    for span in LPPLS_SPANS:
        try:row=lppls_window(close.iloc[-span-1:].to_numpy(),seed+span)
        except (ValueError,RuntimeError,np.linalg.LinAlgError,InfeasibleTestException) as exc:
            row={'span':span,'complete':True,'qualified_positive':False,'qualified_negative':False,'failure':str(exc)}
        rows.append(row)
    confidence=lppls_confidence(rows)
    if all('failure' in r for r in rows):confidence={'positive':None,'negative':None}
    return {'version':VERSION,'train_start':str(close.index[-751].date()),'train_end':str(close.index[-1].date()),
            'seed':seed,'conventions':LPPLS_CONVENTIONS,'attempted_windows':141,'fits':rows,
            'qualified_fraction':confidence['positive'],'negative_fraction':confidence['negative'],
            'converged_windows':sum('failure' not in r and r['complete'] for r in rows),
            'incomplete_windows':sum(not r['complete'] for r in rows),'valid_sessions':0,
            'meaning':'Qualified fraction across all141 nested windows; documented source ambiguities remain; not crash probability.'}
