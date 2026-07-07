import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_service.dart';
import 'result_screen.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {

  bool loading = false;

  Future pickImage() async {

    final picker = ImagePicker();

    final file =
        await picker.pickImage(source: ImageSource.camera);

    if (file == null) return;

    setState(() {
      loading = true;
    });

    final result =
        await ApiService.detectImage(File(file.path));

    setState(() {
      loading = false;
    });

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ResultScreen(result: result),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {

    return Scaffold(
      appBar: AppBar(
        title: const Text("Scan Sampah"),
      ),
      body: Center(
        child: loading
            ? const CircularProgressIndicator()
            : ElevatedButton(
                onPressed: pickImage,
                child: const Text("BUKA KAMERA"),
              ),
      ),
    );
  }
}