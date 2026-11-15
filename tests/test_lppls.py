import math
import unittest
import numpy as np
import pandas as pd
import lppls_confidence_indicator as models

class LPPLSReferenceTests(unittest.TestCase):
    def test_linear_coefficients_and_price_scaling(self):
        t=np.arange(80,dtype=float);tc=100.;m=.5;omega=8.
        d=tc-t;f=d**m
        coefficients=np.array([5.,-.2,.01,-.02])
        y=coefficients[0]+coefficients[1]*f+f*(coefficients[2]*np.cos(omega*np.log(d))+coefficients[3]*np.sin(omega*np.log(d)))
        fit,pred,error=models.lppls_linear(t,y,tc,m,omega)
        np.testing.assert_allclose(fit,coefficients,atol=1e-12)
        np.testing.assert_allclose(pred,y,atol=1e-12)
        self.assertLess(error,1e-20)
        shifted,_,_=models.lppls_linear(t,y+np.log(3),tc,m,omega)
        np.testing.assert_allclose(shifted,coefficients+[np.log(3),0,0,0],atol=1e-12)

    def test_window_endpoints_and_denominator(self):
        self.assertEqual(len(models.LPPLS_SPANS),141)
        self.assertEqual(models.LPPLS_SPANS[0],750)
        self.assertEqual(models.LPPLS_SPANS[-1],50)
        rows=[{'qualified_positive':True,'qualified_negative':False,'complete':True},
              {'qualified_positive':False,'qualified_negative':False,'complete':True},
              {'qualified_positive':False,'qualified_negative':True,'complete':True}]
        result=models.lppls_confidence(rows)
        self.assertEqual(result['positive'],1/3)
        self.assertEqual(result['negative'],1/3)
        rows[1]['complete']=False
        self.assertIsNone(models.lppls_confidence(rows)['positive'])

    def test_filter_boundaries(self):
        row={'m':.5,'omega':8.,'tc':110.,'b':-.2,'damping':1.,'oscillations':2.5,
             'relative_error':.15,'lomb_p':.1,'adf_p':.1,'pp_p':.1}
        self.assertTrue(models.lppls_qualified(row,0.,100.))
        for name,value in [('m',.009),('omega',25.01),('tc',120.01),('damping',.999),
                           ('oscillations',2.49),('relative_error',.151),('lomb_p',.101),('adf_p',.101),('pp_p',.101)]:
            with self.subTest(name=name):self.assertFalse(models.lppls_qualified(dict(row,**{name:value}),0.,100.))

    def test_real_solver_filters_and_serialization(self):
        import json
        from importlib.util import find_spec
        if not find_spec('astropy') or not find_spec('cma'):self.skipTest('optional gauge extra')
        rng=np.random.default_rng(137);x=np.arange(150);d=180-x
        prices=np.exp(5-.1*d**.5+.003*d**.5*np.cos(8*np.log(d))+.005*rng.normal(size=len(x)))
        first=models.lppls_window(prices)
        self.assertTrue(first['complete'])
        self.assertGreater(first['evaluations'],0)
        for name in ('lomb_p','adf_p','pp_p'):self.assertTrue(0<=first[name]<=1)
        json.dumps(first,allow_nan=False)
        self.assertEqual(first,models.lppls_window(prices))
        from concurrent.futures import ProcessPoolExecutor
        from multiprocessing import get_context
        with ProcessPoolExecutor(max_workers=1,mp_context=get_context('spawn')) as pool:
            self.assertEqual(first,pool.submit(models.lppls_window,prices).result())

    def test_solver_list_valued_stopping_diagnostic(self):
        from importlib.util import find_spec
        if not find_spec('astropy') or not find_spec('cma'):self.skipTest('optional gauge extra')
        import cma,json
        from unittest.mock import patch
        stop=cma.CMAEvolutionStrategy.stop
        def with_list(instance,*args,**kwargs):
            result=stop(instance,*args,**kwargs)
            return {**result,'tolxstagnation':[1e-9,20,.1]} if result else result
        rng=np.random.default_rng(137);x=np.arange(150);d=180-x
        prices=np.exp(5-.1*d**.5+.003*d**.5*np.cos(8*np.log(d))+.005*rng.normal(size=len(x)))
        with patch.object(cma.CMAEvolutionStrategy,'stop',with_list):result=models.lppls_window(prices)
        self.assertIsInstance(result['stop']['tolxstagnation'],str)
        json.dumps(result,allow_nan=False)
