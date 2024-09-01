import 'package:dio/dio.dart';
import 'dart:io';

class VideoUploadService {
  final Dio _dio = Dio();

  Future<List<String>> uploadVideo(String url, File videoFile, String filename) async {
    FormData formData = FormData.fromMap({
      "video": await MultipartFile.fromFile(videoFile.path, filename: filename), 
    });

    final response = await _dio.post(url, data: formData);

    if (response.statusCode == 200) {
      return List<String>.from(response.data);
    } else {
      throw Exception('Failed to upload video');
    }
  }
}
