#!/bin/bash

# Windows 11 Hardware Compatibility Checker and Upgrade Guide
# Run this script in Git Bash on Windows

echo "========================================"
echo "Windows 11 Hardware Compatibility Check"
echo "========================================"
echo ""

# Create output directory
mkdir -p ~/win11_check_results
cd ~/win11_check_results

# Function to check if running on Windows
check_windows() {
    if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "cygwin" ]]; then
        echo "ERROR: This script must be run on Windows with Git Bash"
        exit 1
    fi
}

# Function to run PowerShell commands from Git Bash
run_powershell() {
    powershell.exe -Command "$1" 2>/dev/null
}

# Function to download PC Health Check tool
download_pc_health_check() {
    echo "📥 Downloading Microsoft PC Health Check tool..."
    
    # Download PC Health Check
    curl -L -o "WindowsPCHealthCheckSetup.msi" \
        "https://aka.ms/GetPCHealthCheckApp" 2>/dev/null
    
    if [ -f "WindowsPCHealthCheckSetup.msi" ]; then
        echo "✅ PC Health Check downloaded successfully"
        echo "   Location: $(pwd)/WindowsPCHealthCheckSetup.msi"
        echo "   Please install and run this tool after the script completes"
    else
        echo "❌ Failed to download PC Health Check tool"
    fi
}

# Function to check system information
check_system_info() {
    echo "🔍 Gathering system information..."
    
    # Get basic system info
    echo "=== SYSTEM INFORMATION ===" > system_report.txt
    run_powershell "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, WindowsBuildLabEx, WindowsInstallationType, TotalPhysicalMemory, CsProcessors, CsSystemType" >> system_report.txt
    
    echo "" >> system_report.txt
    echo "=== CPU INFORMATION ===" >> system_report.txt
    run_powershell "Get-WmiObject -Class Win32_Processor | Select-Object Name, Manufacturer, Family, Model, Stepping, MaxClockSpeed, NumberOfCores, NumberOfLogicalProcessors" >> system_report.txt
    
    echo "" >> system_report.txt
    echo "=== MEMORY INFORMATION ===" >> system_report.txt
    run_powershell "Get-WmiObject -Class Win32_PhysicalMemory | Select-Object Capacity, Speed, Manufacturer, PartNumber" >> system_report.txt
    
    echo "" >> system_report.txt
    echo "=== MOTHERBOARD INFORMATION ===" >> system_report.txt
    run_powershell "Get-WmiObject -Class Win32_BaseBoard | Select-Object Manufacturer, Product, Version, SerialNumber" >> system_report.txt
    
    echo "" >> system_report.txt
    echo "=== BIOS/UEFI INFORMATION ===" >> system_report.txt
    run_powershell "Get-WmiObject -Class Win32_BIOS | Select-Object Manufacturer, Name, Version, ReleaseDate, SMBIOSBIOSVersion" >> system_report.txt
    
    echo "✅ System information saved to system_report.txt"
}

# Function to check TPM status
check_tpm() {
    echo "🔐 Checking TPM status..."
    
    echo "=== TPM INFORMATION ===" > tpm_report.txt
    
    # Check TPM using multiple methods
    echo "Method 1 - TPM Management Console:" >> tpm_report.txt
    run_powershell "Get-Tpm" >> tpm_report.txt 2>/dev/null
    
    echo "" >> tpm_report.txt
    echo "Method 2 - WMI Query:" >> tpm_report.txt
    run_powershell "Get-WmiObject -Namespace 'Root\CIMv2\Security\MicrosoftTpm' -Class Win32_Tpm" >> tpm_report.txt 2>/dev/null
    
    echo "" >> tpm_report.txt
    echo "Method 3 - Registry Check:" >> tpm_report.txt
    run_powershell "Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\TPM\Parameters' -ErrorAction SilentlyContinue" >> tpm_report.txt 2>/dev/null
    
    echo "✅ TPM information saved to tpm_report.txt"
}

# Function to check Secure Boot status
check_secure_boot() {
    echo "🔒 Checking Secure Boot status..."
    
    echo "=== SECURE BOOT INFORMATION ===" > secure_boot_report.txt
    run_powershell "Confirm-SecureBootUEFI" >> secure_boot_report.txt 2>/dev/null
    
    echo "" >> secure_boot_report.txt
    echo "UEFI Firmware Variables:" >> secure_boot_report.txt
    run_powershell "Get-SecureBootUEFI -Name PK" >> secure_boot_report.txt 2>/dev/null
    
    echo "✅ Secure Boot information saved to secure_boot_report.txt"
}

# Function to check storage
check_storage() {
    echo "💾 Checking storage configuration..."
    
    echo "=== STORAGE INFORMATION ===" > storage_report.txt
    echo "Disk Information:" >> storage_report.txt
    run_powershell "Get-Disk | Select-Object Number, FriendlyName, Size, PartitionStyle, HealthStatus" >> storage_report.txt
    
    echo "" >> storage_report.txt
    echo "Partition Information:" >> storage_report.txt
    run_powershell "Get-Partition | Select-Object DiskNumber, PartitionNumber, Type, Size, DriveLetter" >> storage_report.txt
    
    echo "✅ Storage information saved to storage_report.txt"
}

# Function to generate upgrade recommendations
generate_recommendations() {
    echo "📋 Generating upgrade recommendations..."
    
    cat > upgrade_recommendations.txt << 'EOF'
WINDOWS 11 HARDWARE UPGRADE RECOMMENDATIONS
==========================================

Based on your system analysis, here are the potential upgrades needed:

1. TPM 2.0 REQUIREMENT
   - Check tpm_report.txt for current TPM status
   - If no TPM found:
     * Look for TPM header on motherboard
     * Purchase TPM 2.0 module ($15-30)
     * Enable fTPM in BIOS if available
   - If TPM 1.2 found: Upgrade to TPM 2.0

2. UEFI FIRMWARE
   - Check system_report.txt for BIOS information
   - Legacy BIOS systems need motherboard replacement
   - Enable UEFI mode in BIOS settings

3. SECURE BOOT
   - Check secure_boot_report.txt
   - Usually just needs to be enabled in BIOS
   - Requires UEFI firmware

4. CPU COMPATIBILITY
   - Check system_report.txt for CPU information
   - Required: 8th gen Intel or 2nd gen AMD Ryzen or newer
   - If incompatible: CPU + Motherboard + RAM upgrade needed

5. MEMORY
   - Minimum: 4GB RAM
   - Recommended: 8GB+ RAM
   - Check system_report.txt for current memory

6. STORAGE
   - Check storage_report.txt for partition style
   - Must use GPT partition style (not MBR)
   - Convert using: diskpart or during clean install

NEXT STEPS:
1. Install and run WindowsPCHealthCheckSetup.msi
2. Review all generated report files
3. Check motherboard manual for TPM header
4. Enter BIOS/UEFI settings to enable:
   - TPM/fTPM
   - UEFI Boot Mode
   - Secure Boot
5. Consider hardware upgrades based on compatibility gaps

COST ESTIMATES:
- TPM 2.0 Module: $15-30
- RAM Upgrade: $30-100
- SSD Upgrade: $50-200
- CPU+Motherboard+RAM: $300-800+
- Complete System: $500-1500+

EOF

    echo "✅ Upgrade recommendations saved to upgrade_recommendations.txt"
}

# Function to create upgrade checklist
create_checklist() {
    echo "📝 Creating upgrade checklist..."
    
    cat > upgrade_checklist.txt << 'EOF'
WINDOWS 11 UPGRADE CHECKLIST
============================

BEFORE STARTING:
□ Backup all important data
□ Note Windows 10 license key
□ Check software compatibility
□ Verify peripheral compatibility

BIOS/UEFI SETTINGS TO CHECK:
□ Enable TPM 2.0 or fTPM
□ Enable UEFI boot mode
□ Enable Secure Boot
□ Disable CSM (Compatibility Support Module)
□ Enable UEFI network boot (if needed)

HARDWARE UPGRADES (if needed):
□ Install TPM 2.0 module
□ Upgrade RAM to 8GB+
□ Install compatible CPU
□ Upgrade motherboard
□ Convert to GPT partition style
□ Install SSD for better performance

VERIFICATION STEPS:
□ Run PC Health Check tool
□ Verify all requirements met
□ Test boot with new settings
□ Backup current system
□ Download Windows 11 ISO

INSTALLATION OPTIONS:
□ Windows Update (if compatible)
□ Media Creation Tool
□ ISO file installation
□ Clean installation

POST-UPGRADE:
□ Install drivers
□ Restore data
□ Install applications
□ Configure settings
□ Run Windows Update

EOF

    echo "✅ Upgrade checklist saved to upgrade_checklist.txt"
}

# Function to create useful scripts
create_helper_scripts() {
    echo "🛠️ Creating helper scripts..."
    
    # Script to convert MBR to GPT
    cat > convert_mbr_to_gpt.txt << 'EOF'
CONVERT MBR TO GPT (CAUTION: BACKUP DATA FIRST!)
===============================================

Method 1 - Using MBR2GPT (Windows 10/11):
1. Open Command Prompt as Administrator
2. Run: mbr2gpt /validate /disk:0
3. If validation passes: mbr2gpt /convert /disk:0

Method 2 - Using Diskpart (DESTRUCTIVE):
1. Boot from Windows installation media
2. Press Shift+F10 to open command prompt
3. Run: diskpart
4. list disk
5. select disk 0 (replace 0 with your disk number)
6. clean
7. convert gpt
8. create partition primary
9. format fs=ntfs quick
10. assign
11. exit

WARNING: Method 2 will erase all data on the disk!
EOF

    # Script to enable TPM in common BIOS
    cat > enable_tpm_guide.txt << 'EOF'
ENABLE TPM IN BIOS/UEFI
=======================

Common BIOS/UEFI Locations:
- Security → TPM Configuration
- Advanced → Trusted Computing
- Security → Secure Boot Configuration
- Advanced → PCH-FW Configuration
- Security → Device Guard

Steps:
1. Restart computer
2. Press BIOS key during boot (F2, F12, Del, etc.)
3. Navigate to Security or Advanced section
4. Look for TPM, Trusted Computing, or Security Device
5. Enable TPM 2.0 or fTPM
6. Save and exit

Common TPM Settings:
- TPM Device: Enabled
- TPM Specification: 2.0
- Firmware TPM: Enabled
- Security Device Support: Enabled

After enabling TPM:
- Boot to Windows
- Run tpm.msc to verify
- Check Device Manager for TPM device
EOF

    echo "✅ Helper scripts created"
}

# Main execution
main() {
    echo "Starting Windows 11 hardware compatibility check..."
    echo "This script will analyze your system and provide upgrade recommendations."
    echo ""
    
    check_windows
    
    echo "Creating analysis reports..."
    echo ""
    
    download_pc_health_check
    echo ""
    
    check_system_info
    echo ""
    
    check_tpm
    echo ""
    
    check_secure_boot
    echo ""
    
    check_storage
    echo ""
    
    generate_recommendations
    echo ""
    
    create_checklist
    echo ""
    
    create_helper_scripts
    echo ""
    
    echo "========================================"
    echo "✅ Analysis Complete!"
    echo "========================================"
    echo ""
    echo "Generated files in $(pwd):"
    echo "- system_report.txt (detailed system information)"
    echo "- tpm_report.txt (TPM status)"
    echo "- secure_boot_report.txt (Secure Boot status)"
    echo "- storage_report.txt (storage configuration)"
    echo "- upgrade_recommendations.txt (specific upgrade advice)"
    echo "- upgrade_checklist.txt (step-by-step checklist)"
    echo "- convert_mbr_to_gpt.txt (storage conversion guide)"
    echo "- enable_tpm_guide.txt (TPM enablement guide)"
    echo "- WindowsPCHealthCheckSetup.msi (Microsoft compatibility tool)"
    echo ""
    echo "Next steps:"
    echo "1. Review all generated reports"
    echo "2. Install and run WindowsPCHealthCheckSetup.msi"
    echo "3. Follow the upgrade checklist"
    echo "4. Make necessary hardware purchases"
    echo "5. Backup your data before making changes"
    echo ""
    echo "⚠️  Remember: Always backup your data before making hardware changes!"
}

# Run the main function
main