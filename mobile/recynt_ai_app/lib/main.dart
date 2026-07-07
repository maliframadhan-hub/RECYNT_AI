import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(const RecyntAI());
}

class RecyntAI extends StatelessWidget {
  const RecyntAI({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Recynt AI',
      theme: AppTheme.darkTheme,
      home: const HomeScreen(),
    );
  }
}