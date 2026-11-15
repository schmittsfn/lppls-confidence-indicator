import SwiftUI

/// Fixed-size editorial illustration; curves are schematic, not market data.
struct HeroView: View {
    private let navy = Color(red: 0.07, green: 0.16, blue: 0.25)
    private let blue = Color(red: 0.31, green: 0.48, blue: 0.61)
    private let red = Color(red: 0.62, green: 0.22, blue: 0.22)

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Rectangle().fill(navy).frame(height: 4)
            HStack(alignment: .top, spacing: 46) {
                VStack(alignment: .leading, spacing: 24) {
                    Text("PRICE DYNAMICS / 03").font(.system(size: 12, weight: .semibold)).tracking(2.5).foregroundStyle(blue)
                    Text("Faster gains.\nGreater fragility?").font(.system(size: 39, design: .serif)).foregroundStyle(navy).lineSpacing(3)
                    Rectangle().fill(red).frame(width: 38, height: 2)
                    Text("An accelerating boom can look strongest\njust as its foundations become less stable.").font(.system(size: 16)).lineSpacing(6).foregroundStyle(navy.opacity(0.8))
                    Spacer()
                }.frame(width: 360, alignment: .leading)
                VStack(spacing: 15) {
                    Canvas { context, size in
                        for fraction in [0.25, 0.5, 0.75] {
                            var grid = Path()
                            grid.move(to: CGPoint(x: 0, y: size.height * fraction))
                            grid.addLine(to: CGPoint(x: size.width, y: size.height * fraction))
                            context.stroke(grid, with: .color(navy.opacity(0.08)), lineWidth: 1)
                        }
                        var path = Path()
            for step in 0...400 {
                let t = Double(step) / 400
                let trend = 0.84 - 0.70 * pow(t, 2.3)
                let wave = (0.012 + 0.025 * t) * sin(10 * t + 17 * t * t * t)
                let point = CGPoint(x: t * size.width, y: (trend + wave) * size.height)
                if step == 0 { path.move(to: point) } else { path.addLine(to: point) }
            }
            context.stroke(path, with: .color(navy), style: StrokeStyle(lineWidth: 2.8, lineCap: .round))
            let finalY = (0.14 + 0.037 * sin(27.0)) * size.height
            let marker = CGRect(x: size.width - 4, y: finalY - 4, width: 8, height: 8)
            context.fill(Path(ellipseIn: marker), with: .color(red))
                    }.frame(height: 285)
                    HStack {
                        Text("A steady beginning")
                        Spacer()
                        Text("An accelerating, oscillating rise")
                    }.font(.system(size: 12)).foregroundStyle(navy.opacity(0.65))
                }.padding(.top, 18)
            }.padding(.horizontal, 48).padding(.top, 42)
            Spacer(minLength: 24)
            Rectangle().fill(navy.opacity(0.15)).frame(height: 1).padding(.horizontal, 48)
            HStack {
                Text("RESEARCH / CONCEPTUAL ILLUSTRATION").tracking(1.4)
                Spacer()
                Text("Schematic only · not a forecast")
            }.font(.system(size: 10)).foregroundStyle(navy.opacity(0.65)).padding(.horizontal, 48).padding(.vertical, 22)
        }.frame(width: 1200, height: 470).background(Color(red: 0.98, green: 0.977, blue: 0.966))
            .environment(\.colorScheme, .light)
    }
}
