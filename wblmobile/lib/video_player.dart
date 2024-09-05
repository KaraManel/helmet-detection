import 'dart:io';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:path/path.dart';
import 'video_upload_service.dart';
import 'package:carousel_slider/carousel_slider.dart';

class VideoPlayerScreen extends StatefulWidget {
  final String videoPath;

  const VideoPlayerScreen({Key? key, required this.videoPath})
      : super(key: key);

  @override
  _VideoPlayerScreenState createState() => _VideoPlayerScreenState();
}

class _VideoPlayerScreenState extends State<VideoPlayerScreen> {
  late VideoPlayerController _controller;
  final VideoUploadService _videoUploadService = VideoUploadService();
  List<dynamic>? _frameFilenames = null;
  bool _isError = false;
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    _controller = VideoPlayerController.file(File(widget.videoPath))
      ..initialize().then((_) {
        setState(() {
          _frameFilenames = [];
        });
        _controller.play();
      });
  }

  @override
  void dispose() {
    _controller.dispose();
    setState(() {
      _frameFilenames = [];
    });
    super.dispose();
  }

  Future<void> _uploadVideo() async {
    setState(() {
      _isProcessing = true;
      _isError = false;
      _frameFilenames = [];
    });

    try {
      // Send the video to the Flask server and receive the response.
      final List<String> encodedImages = await _videoUploadService.uploadVideo(
        'http://192.168.1.72:5000/process_video',
        File(widget.videoPath),
        basename(widget.videoPath),
      );

      // Check if the response contains the string indicating all helmets were worn.
      if (encodedImages.contains("All helmets were worn")) {
        setState(() {
          _frameFilenames = ["All helmets were worn"];
          _isProcessing = false;
        });
      } else {
        // Decode the base64 strings into images.
        final List<Uint8List> decodedImages = encodedImages.map((imageString) {
          return base64Decode(imageString);
        }).toList();

        setState(() {
          _frameFilenames = decodedImages;
          _isProcessing = false;
        });
      }
    } catch (e) {
      setState(() {
        _isError = true;
        _isProcessing = false;
      });
    }
  }

  Future<void> clearImageCache() async {
    PaintingBinding.instance.imageCache.clear();
    PaintingBinding.instance.imageCache.clearLiveImages();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          _controller.value.isInitialized
              ? SizedBox.expand(
                  child: FittedBox(
                    fit: BoxFit.cover,
                    child: SizedBox(
                      width: _controller.value.size.width,
                      height: _controller.value.size.height,
                      child: VideoPlayer(_controller),
                    ),
                  ),
                )
              : Center(child: CircularProgressIndicator()),
          Positioned(
            top: 50,
            left: 10,
            child: GestureDetector(
              onTap: () {
                Navigator.of(context).pop();
              },
              child: Icon(
                Icons.close,
                color: Colors.white,
                size: 30.0,
              ),
            ),
          ),
          Positioned(
            bottom: 20,
            left: 20,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                SizedBox(width: 120),
                ElevatedButton(
                  onPressed: _isProcessing ? null : _uploadVideo,
                  child: Text('Process Video'),
                ),
                SizedBox(width: 30),
                FloatingActionButton(
                  onPressed: () {
                    setState(() {
                      _controller.value.isPlaying
                          ? _controller.pause()
                          : _controller.play();
                    });
                  },
                  child: Icon(
                    _controller.value.isPlaying
                        ? Icons.pause
                        : Icons.play_arrow,
                  ),
                ),
              ],
            ),
          ),
          if (_isProcessing)
            Center(
              child: CircularProgressIndicator(),
            ),
          if (_frameFilenames != null && _frameFilenames!.isNotEmpty)
            _frameFilenames!.contains("All helmets were worn")
                ? Center(
                    child: Text(
                      'No frame found.',
                      style: TextStyle(color: Colors.red, fontSize: 18),
                    ),
                  )
                : Center(
                    child: CarouselSlider(
                      options: CarouselOptions(
                        height: MediaQuery.of(context).size.height * 0.7,
                        viewportFraction: 1.0,
                        enableInfiniteScroll: false,
                        initialPage: 0,
                      ),
                      items: _frameFilenames!.map((frame) {
                        return Builder(
                          builder: (BuildContext context) {
                            return frame is Uint8List
                                ? Image.memory(
                                    frame,
                                    fit: BoxFit.cover,
                                  )
                                : Container();
                          },
                        );
                      }).toList(),
                    ),
                  ),
          if (_isError)
            Center(
              child: Text(
                'Error processing video.',
                style: TextStyle(color: Colors.red, fontSize: 18),
              ),
            ),
        ],
      ),
    );
  }
}
