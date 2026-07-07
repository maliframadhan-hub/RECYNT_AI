import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

class ApiService {

  static const String apiUrl =
      "http://YOUR_SERVER_IP:5000/detect";

  static Future<Map<String, dynamic>> detectImage(
      File image) async {

    var request = http.MultipartRequest(
      "POST",
      Uri.parse(apiUrl),
    );

    request.files.add(
      await http.MultipartFile.fromPath(
        "image",
        image.path,
      ),
    );

    final response =
        await request.send();

    final data =
        await response.stream.bytesToString();

    return jsonDecode(data);
  }
}