import 'package:flutter/material.dart';

class ResultScreen extends StatelessWidget {

  final Map<String, dynamic> result;

  const ResultScreen({
    super.key,
    required this.result,
  });

  @override
  Widget build(BuildContext context) {

    return Scaffold(
      appBar: AppBar(
        title: const Text("Hasil Deteksi"),
      ),
      body: Center(
        child: Card(
          color: const Color(0xff0B1612),
          margin: const EdgeInsets.all(20),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [

                const Icon(
                  Icons.recycling,
                  size: 80,
                  color: Color(0xff00FF99),
                ),

                const SizedBox(height: 20),

                Text(
                  result["class"],
                  style: const TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                const SizedBox(height: 10),

                Text(
                  "Confidence ${(result["confidence"] * 100).toStringAsFixed(2)}%",
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}