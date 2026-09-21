import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

// Original vector artwork for Oracle Cinema.
let size = 1024
let space = CGColorSpaceCreateDeviceRGB()
let context = CGContext(data: nil, width: size, height: size, bitsPerComponent: 8,
  bytesPerRow: size * 4, space: space,
  bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
let colors = [CGColor(red: 0.10, green: 0.14, blue: 0.21, alpha: 1),
              CGColor(red: 0.025, green: 0.035, blue: 0.06, alpha: 1)]
let gradient = CGGradient(colorsSpace: space, colors: colors as CFArray,
                          locations: [0, 1])!
context.drawLinearGradient(gradient, start: CGPoint(x: 0, y: 1024),
  end: CGPoint(x: 1024, y: 0), options: [.drawsBeforeStartLocation, .drawsAfterEndLocation])
let gold = CGColor(red: 0.94, green: 0.68, blue: 0.32, alpha: 1)
context.setStrokeColor(gold)
context.setLineWidth(30)
context.addPath(CGPath(roundedRect: CGRect(x: 206, y: 218, width: 612, height: 588),
  cornerWidth: 104, cornerHeight: 104, transform: nil))
context.strokePath()
context.setFillColor(gold)
for x in [248, 730] {
  for y in stride(from: 310, through: 662, by: 88) {
    context.addPath(CGPath(roundedRect: CGRect(x: x, y: y, width: 46, height: 46),
      cornerWidth: 12, cornerHeight: 12, transform: nil))
    context.fillPath()
  }
}
context.setFillColor(CGColor(red: 1, green: 0.95, blue: 0.86, alpha: 1))
let play = CGMutablePath()
play.move(to: CGPoint(x: 435, y: 365))
play.addLine(to: CGPoint(x: 435, y: 659))
play.addCurve(to: CGPoint(x: 464, y: 675), control1: CGPoint(x: 435, y: 679),
              control2: CGPoint(x: 449, y: 684))
play.addLine(to: CGPoint(x: 661, y: 529))
play.addCurve(to: CGPoint(x: 661, y: 495), control1: CGPoint(x: 679, y: 517),
              control2: CGPoint(x: 679, y: 507))
play.addLine(to: CGPoint(x: 464, y: 349))
play.addCurve(to: CGPoint(x: 435, y: 365), control1: CGPoint(x: 449, y: 340),
              control2: CGPoint(x: 435, y: 345))
play.closeSubpath()
context.addPath(play)
context.fillPath()
let output = URL(fileURLWithPath: CommandLine.arguments.dropFirst().first ?? "assets/oracle/icon.png")
try FileManager.default.createDirectory(at: output.deletingLastPathComponent(), withIntermediateDirectories: true)
let destination = CGImageDestinationCreateWithURL(output as CFURL, UTType.png.identifier as CFString, 1, nil)!
CGImageDestinationAddImage(destination, context.makeImage()!, nil)
precondition(CGImageDestinationFinalize(destination))
print(output.path)
