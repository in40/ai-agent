#!/bin/bash
# Install system dependencies for OCR and PDF processing

set -e  # Exit on error

echo "Installing OCR and PDF processing dependencies..."

# Update package list
sudo apt-get update

# Install Tesseract OCR with Russian language support
echo "Installing Tesseract OCR..."
sudo apt-get install -y tesseract-ocr
sudo apt-get install -y tesseract-ocr-rus
sudo apt-get install -y tesseract-ocr-eng

# Install poppler-utils for PDF to image conversion
echo "Installing poppler-utils..."
sudo apt-get install -y poppler-utils

# Verify installation
echo "Verifying installation..."
tesseract --version
tesseract --list-langs | grep -E "rus|eng" || echo "Warning: Language packs may not be installed correctly"

echo "✓ OCR dependencies installed successfully!"
