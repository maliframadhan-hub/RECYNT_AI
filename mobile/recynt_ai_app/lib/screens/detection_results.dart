class DetectionResult {

  final String label;
  final double confidence;

  DetectionResult({
    required this.label,
    required this.confidence,
  });

  factory DetectionResult.fromJson(
      Map<String, dynamic> json) {

    return DetectionResult(
      label: json["class"],
      confidence:
          json["confidence"].toDouble(),
    );
  }
}