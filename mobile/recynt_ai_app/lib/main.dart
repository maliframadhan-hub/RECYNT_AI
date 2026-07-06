import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const RecyntApp());
}

class RecyntApp extends StatelessWidget {
  const RecyntApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RECYNT AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const SplashScreen(),
    );
  }
}
