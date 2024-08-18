import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:path/path.dart' show join;
import 'package:path_provider/path_provider.dart';
import 'package:wblmobile/video_player.dart';

class VideoScreen extends StatefulWidget {
  @override
  _VideoScreenState createState() => _VideoScreenState();
}

class _VideoScreenState extends State<VideoScreen> {
  CameraController? _controller;
  List<CameraDescription>? cameras;
  bool isRecording = false;

  @override
  void initState() {
    super.initState();
    initializeCamera();
  }

  Future<void> initializeCamera() async {
    cameras = await availableCameras();
    _controller = CameraController(
      cameras!.first,
      ResolutionPreset.high,
    );

    await _controller!.initialize();
    setState(() {});
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> startRecording() async {
  if (!_controller!.value.isRecordingVideo) {
    await _controller!.startVideoRecording();
    setState(() {
      isRecording = true;
    });
  }
}

Future<void> stopRecording() async {
  if (_controller!.value.isRecordingVideo) {
    XFile videoFile = await _controller!.stopVideoRecording();
    setState(() {
      isRecording = false;
    });

    print('Video recorded to: ${videoFile.path}');
      Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => VideoPlayerScreen(videoPath: videoFile.path),
      ),
    );
  }
}


  @override
  Widget build(BuildContext context) {
    if (_controller == null || !_controller!.value.isInitialized) {
      return Center(child: CircularProgressIndicator());
    }

    return Scaffold(
      body: Stack(
        children: [
          CameraPreview(_controller!),
          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: FloatingActionButton(
                onPressed: isRecording ? stopRecording : startRecording,
                backgroundColor: isRecording ? Colors.red : Colors.white,
                child: Icon(
                  isRecording ? Icons.stop : Icons.videocam,
                  color: isRecording ? Colors.white : Colors.black,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
