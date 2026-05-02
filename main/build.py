"""
MagicHand Build Script
Automates the build process for creating the executable and installer
"""

import os
import shutil
import subprocess
import sys

def clean_build():
    """Remove previous build artifacts"""
    print("🧹 Cleaning previous builds...")
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")
    print("✅ Clean complete\n")

def create_icon():
    """Create icon from generated image"""
    print("🎨 Creating application icon...")
    try:
        from PIL import Image
        
        # Check if icon already exists
        if os.path.exists('icon.ico'):
            print("   Icon already exists, skipping...")
            return
        
        # Use the generated icon image
        icon_path = r"C:\Users\mdrez\.gemini\antigravity\brain\a9a1356d-61dd-4597-877b-8ad3d1f85c49\magichand_icon_1766439589809.png"
        
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
            img = img.resize((256, 256), Image.Resampling.LANCZOS)
            img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print("   ✅ Icon created successfully")
        else:
            print("   ⚠️  Icon image not found, using default")
    except Exception as e:
        print(f"   ⚠️  Error creating icon: {e}")

def create_version_info():
    """Create version information file"""
    print("📝 Creating version info...")
    version_info = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'MagicHand'),
        StringStruct(u'FileDescription', u'MagicHand Gesture Control'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'MagicHand'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2025'),
        StringStruct(u'OriginalFilename', u'MagicHand.exe'),
        StringStruct(u'ProductName', u'MagicHand'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    print("   ✅ Version info created\n")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable with PyInstaller...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', '--clean', 'MagicHand.spec'],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("   ✅ Executable built successfully\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Build failed: {e}")
        print(e.stderr)
        return False

def create_installer():
    """Create installer using Inno Setup (if available)"""
    print("📦 Creating installer...")
    
    # Check if Inno Setup is installed
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
    ]
    
    iscc_path = None
    for path in inno_paths:
        if os.path.exists(path):
            iscc_path = path
            break
    
    if not iscc_path:
        print("   ⚠️  Inno Setup not found. Skipping installer creation.")
        print("   💡 Install Inno Setup from: https://jrsoftware.org/isdl.php")
        return False
    
    if not os.path.exists('installer.iss'):
        print("   ⚠️  installer.iss not found. Skipping installer creation.")
        return False
    
    try:
        result = subprocess.run(
            [iscc_path, 'installer.iss'],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("   ✅ Installer created successfully\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Installer creation failed: {e}")
        print(e.stderr)
        return False

def main():
    """Main build process"""
    print("=" * 60)
    print("🪄  MagicHand Build Script")
    print("=" * 60)
    print()
    
    # Step 1: Clean
    clean_build()
    
    # Step 2: Create icon
    create_icon()
    
    # Step 3: Create version info
    create_version_info()
    
    # Step 4: Build executable
    if not build_executable():
        print("\n❌ Build failed!")
        sys.exit(1)
    
    # Step 5: Create installer (optional)
    create_installer()
    
    print("=" * 60)
    print("✅ Build complete!")
    print("=" * 60)
    print()
    print("📁 Output:")
    print(f"   Executable: dist/MagicHand.exe")
    if os.path.exists('Output'):
        print(f"   Installer:  Output/MagicHandSetup.exe")
    print()

if __name__ == "__main__":
    main()
