#!/bin/bash
#
# Recovery Script for Pre-Production Backup
# This script moves files back to their original locations
#

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         File Recovery Script                                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Confirm recovery
read -p "This will move files back to their original locations. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Recovery cancelled."
    exit 0
fi

echo ""
echo "Starting recovery..."
echo ""

if [ -f "$SCRIPT_DIR/downloads/230728-56-1_1.pdf" ]; then
    echo "Restoring: 230728-56-1_1.pdf"
    mv "$SCRIPT_DIR/downloads/230728-56-1_1.pdf" "/root/qwen/ai_agent/downloads/230728-56-1_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/230728-56-1_2.pdf" ]; then
    echo "Restoring: 230728-56-1_2.pdf"
    mv "$SCRIPT_DIR/downloads/230728-56-1_2.pdf" "/root/qwen/ai_agent/downloads/230728-56-1_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/230728-56-1_3.pdf" ]; then
    echo "Restoring: 230728-56-1_3.pdf"
    mv "$SCRIPT_DIR/downloads/230728-56-1_3.pdf" "/root/qwen/ai_agent/downloads/230728-56-1_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/230728-56-1.pdf" ]; then
    echo "Restoring: 230728-56-1.pdf"
    mv "$SCRIPT_DIR/downloads/230728-56-1.pdf" "/root/qwen/ai_agent/downloads/230728-56-1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/4294852100.pdf" ]; then
    echo "Restoring: 4294852100.pdf"
    mv "$SCRIPT_DIR/downloads/4294852100.pdf" "/root/qwen/ai_agent/downloads/4294852100.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost1759_0-87.pdf" ]; then
    echo "Restoring: gost1759_0-87.pdf"
    mv "$SCRIPT_DIR/downloads/gost1759_0-87.pdf" "/root/qwen/ai_agent/downloads/gost1759_0-87.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost_2.105_95.pdf" ]; then
    echo "Restoring: gost_2.105_95.pdf"
    mv "$SCRIPT_DIR/downloads/gost_2.105_95.pdf" "/root/qwen/ai_agent/downloads/gost_2.105_95.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost_25346-89.pdf" ]; then
    echo "Restoring: gost_25346-89.pdf"
    mv "$SCRIPT_DIR/downloads/gost_25346-89.pdf" "/root/qwen/ai_agent/downloads/gost_25346-89.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost_25347-82.pdf" ]; then
    echo "Restoring: gost_25347-82.pdf"
    mv "$SCRIPT_DIR/downloads/gost_25347-82.pdf" "/root/qwen/ai_agent/downloads/gost_25347-82.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_10.pdf" ]; then
    echo "Restoring: gost-34_10.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_10.pdf" "/root/qwen/ai_agent/downloads/gost-34_10.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_1.pdf" ]; then
    echo "Restoring: gost-34_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_1.pdf" "/root/qwen/ai_agent/downloads/gost-34_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_2.pdf" ]; then
    echo "Restoring: gost-34_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_2.pdf" "/root/qwen/ai_agent/downloads/gost-34_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_3.pdf" ]; then
    echo "Restoring: gost-34_3.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_3.pdf" "/root/qwen/ai_agent/downloads/gost-34_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_4.pdf" ]; then
    echo "Restoring: gost-34_4.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_4.pdf" "/root/qwen/ai_agent/downloads/gost-34_4.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_5.pdf" ]; then
    echo "Restoring: gost-34_5.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_5.pdf" "/root/qwen/ai_agent/downloads/gost-34_5.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_6.pdf" ]; then
    echo "Restoring: gost-34_6.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_6.pdf" "/root/qwen/ai_agent/downloads/gost-34_6.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_7.pdf" ]; then
    echo "Restoring: gost-34_7.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_7.pdf" "/root/qwen/ai_agent/downloads/gost-34_7.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_8.pdf" ]; then
    echo "Restoring: gost-34_8.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_8.pdf" "/root/qwen/ai_agent/downloads/gost-34_8.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34_9.pdf" ]; then
    echo "Restoring: gost-34_9.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34_9.pdf" "/root/qwen/ai_agent/downloads/gost-34_9.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-34.pdf" ]; then
    echo "Restoring: gost-34.pdf"
    mv "$SCRIPT_DIR/downloads/gost-34.pdf" "/root/qwen/ai_agent/downloads/gost-34.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/GOST_7.0.97-2016.pdf" ]; then
    echo "Restoring: GOST_7.0.97-2016.pdf"
    mv "$SCRIPT_DIR/downloads/GOST_7.0.97-2016.pdf" "/root/qwen/ai_agent/downloads/GOST_7.0.97-2016.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/GOST_R_2.105-2019.pdf" ]; then
    echo "Restoring: GOST_R_2.105-2019.pdf"
    mv "$SCRIPT_DIR/downloads/GOST_R_2.105-2019.pdf" "/root/qwen/ai_agent/downloads/GOST_R_2.105-2019.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_10.pdf" ]; then
    echo "Restoring: gost-r-34_10.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_10.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_10.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_11.pdf" ]; then
    echo "Restoring: gost-r-34_11.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_11.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_11.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_12.pdf" ]; then
    echo "Restoring: gost-r-34_12.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_12.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_12.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_1.pdf" ]; then
    echo "Restoring: gost-r-34_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_2.pdf" ]; then
    echo "Restoring: gost-r-34_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_3.pdf" ]; then
    echo "Restoring: gost-r-34_3.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_3.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_4.pdf" ]; then
    echo "Restoring: gost-r-34_4.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_4.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_4.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_5.pdf" ]; then
    echo "Restoring: gost-r-34_5.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_5.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_5.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_6.pdf" ]; then
    echo "Restoring: gost-r-34_6.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_6.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_6.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_7.pdf" ]; then
    echo "Restoring: gost-r-34_7.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_7.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_7.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_8.pdf" ]; then
    echo "Restoring: gost-r-34_8.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_8.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_8.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34_9.pdf" ]; then
    echo "Restoring: gost-r-34_9.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34_9.pdf" "/root/qwen/ai_agent/downloads/gost-r-34_9.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-34.pdf" ]; then
    echo "Restoring: gost-r-34.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-34.pdf" "/root/qwen/ai_agent/downloads/gost-r-34.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-50739-1995=edt2006_1.pdf" ]; then
    echo "Restoring: gost-r-50739-1995=edt2006_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-50739-1995=edt2006_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-50739-1995=edt2006_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-50739-1995=edt2006_2.pdf" ]; then
    echo "Restoring: gost-r-50739-1995=edt2006_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-50739-1995=edt2006_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-50739-1995=edt2006_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-50739-1995=edt2006.pdf" ]; then
    echo "Restoring: gost-r-50739-1995=edt2006.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-50739-1995=edt2006.pdf" "/root/qwen/ai_agent/downloads/gost-r-50739-1995=edt2006.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-50922-2006_1.pdf" ]; then
    echo "Restoring: gost-r-50922-2006_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-50922-2006_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-50922-2006_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-50922-2006_2.pdf" ]; then
    echo "Restoring: gost-r-50922-2006_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-50922-2006_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-50922-2006_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-50922-2006.pdf" ]; then
    echo "Restoring: gost-r-50922-2006.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-50922-2006.pdf" "/root/qwen/ai_agent/downloads/gost-r-50922-2006.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-51275-2006=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-51275-2006=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-51275-2006=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-51275-2006=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-51275-2006=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-51275-2006=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-51275-2006=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-51275-2006=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-51275-2006=edt2018.pdf" ]; then
    echo "Restoring: gost-r-51275-2006=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-51275-2006=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-51275-2006=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-51583-2014=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-51583-2014=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-51583-2014=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-51583-2014=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-51583-2014=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-51583-2014=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-51583-2014=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-51583-2014=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-51583-2014=edt2018.pdf" ]; then
    echo "Restoring: gost-r-51583-2014=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-51583-2014=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-51583-2014=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52069_1.pdf" ]; then
    echo "Restoring: gost-r-52069_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52069_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-52069_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52069_2.pdf" ]; then
    echo "Restoring: gost-r-52069_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52069_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-52069_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52069.pdf" ]; then
    echo "Restoring: gost-r-52069.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52069.pdf" "/root/qwen/ai_agent/downloads/gost-r-52069.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52447-2005=edt2020_1.pdf" ]; then
    echo "Restoring: gost-r-52447-2005=edt2020_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52447-2005=edt2020_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-52447-2005=edt2020_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52447-2005=edt2020_2.pdf" ]; then
    echo "Restoring: gost-r-52447-2005=edt2020_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52447-2005=edt2020_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-52447-2005=edt2020_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52447-2005=edt2020.pdf" ]; then
    echo "Restoring: gost-r-52447-2005=edt2020.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52447-2005=edt2020.pdf" "/root/qwen/ai_agent/downloads/gost-r-52447-2005=edt2020.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52448-2005=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-52448-2005=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52448-2005=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-52448-2005=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52448-2005=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-52448-2005=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52448-2005=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-52448-2005=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52448-2005=edt2018.pdf" ]; then
    echo "Restoring: gost-r-52448-2005=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52448-2005=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-52448-2005=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_10.pdf" ]; then
    echo "Restoring: gost-r-52633_10.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_10.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_10.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_11.pdf" ]; then
    echo "Restoring: gost-r-52633_11.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_11.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_11.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_12.pdf" ]; then
    echo "Restoring: gost-r-52633_12.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_12.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_12.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_13.pdf" ]; then
    echo "Restoring: gost-r-52633_13.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_13.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_13.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_14.pdf" ]; then
    echo "Restoring: gost-r-52633_14.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_14.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_14.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_15.pdf" ]; then
    echo "Restoring: gost-r-52633_15.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_15.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_15.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_16.pdf" ]; then
    echo "Restoring: gost-r-52633_16.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_16.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_16.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_1.pdf" ]; then
    echo "Restoring: gost-r-52633_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_2.pdf" ]; then
    echo "Restoring: gost-r-52633_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_3.pdf" ]; then
    echo "Restoring: gost-r-52633_3.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_3.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_4.pdf" ]; then
    echo "Restoring: gost-r-52633_4.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_4.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_4.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_5.pdf" ]; then
    echo "Restoring: gost-r-52633_5.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_5.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_5.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_6.pdf" ]; then
    echo "Restoring: gost-r-52633_6.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_6.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_6.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_7.pdf" ]; then
    echo "Restoring: gost-r-52633_7.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_7.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_7.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_8.pdf" ]; then
    echo "Restoring: gost-r-52633_8.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_8.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_8.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633_9.pdf" ]; then
    echo "Restoring: gost-r-52633_9.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633_9.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633_9.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52633.pdf" ]; then
    echo "Restoring: gost-r-52633.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52633.pdf" "/root/qwen/ai_agent/downloads/gost-r-52633.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52863-2007=edt2020_1.pdf" ]; then
    echo "Restoring: gost-r-52863-2007=edt2020_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52863-2007=edt2020_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-52863-2007=edt2020_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52863-2007=edt2020_2.pdf" ]; then
    echo "Restoring: gost-r-52863-2007=edt2020_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52863-2007=edt2020_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-52863-2007=edt2020_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-52863-2007=edt2020.pdf" ]; then
    echo "Restoring: gost-r-52863-2007=edt2020.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-52863-2007=edt2020.pdf" "/root/qwen/ai_agent/downloads/gost-r-52863-2007=edt2020.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53109-2008=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-53109-2008=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53109-2008=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-53109-2008=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53109-2008=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-53109-2008=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53109-2008=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-53109-2008=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53109-2008=edt2018.pdf" ]; then
    echo "Restoring: gost-r-53109-2008=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53109-2008=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-53109-2008=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53110-2008=edt2020_1.pdf" ]; then
    echo "Restoring: gost-r-53110-2008=edt2020_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53110-2008=edt2020_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-53110-2008=edt2020_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53110-2008=edt2020_2.pdf" ]; then
    echo "Restoring: gost-r-53110-2008=edt2020_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53110-2008=edt2020_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-53110-2008=edt2020_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53110-2008=edt2020.pdf" ]; then
    echo "Restoring: gost-r-53110-2008=edt2020.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53110-2008=edt2020.pdf" "/root/qwen/ai_agent/downloads/gost-r-53110-2008=edt2020.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53111-2008=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-53111-2008=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53111-2008=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-53111-2008=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53111-2008=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-53111-2008=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53111-2008=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-53111-2008=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53111-2008=edt2018.pdf" ]; then
    echo "Restoring: gost-r-53111-2008=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53111-2008=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-53111-2008=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53112-2008=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-53112-2008=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53112-2008=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-53112-2008=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53112-2008=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-53112-2008=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53112-2008=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-53112-2008=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53112-2008=edt2018.pdf" ]; then
    echo "Restoring: gost-r-53112-2008=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53112-2008=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-53112-2008=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53113_1.pdf" ]; then
    echo "Restoring: gost-r-53113_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53113_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-53113_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53113_2.pdf" ]; then
    echo "Restoring: gost-r-53113_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53113_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-53113_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53113_3.pdf" ]; then
    echo "Restoring: gost-r-53113_3.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53113_3.pdf" "/root/qwen/ai_agent/downloads/gost-r-53113_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53113_4.pdf" ]; then
    echo "Restoring: gost-r-53113_4.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53113_4.pdf" "/root/qwen/ai_agent/downloads/gost-r-53113_4.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53113_5.pdf" ]; then
    echo "Restoring: gost-r-53113_5.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53113_5.pdf" "/root/qwen/ai_agent/downloads/gost-r-53113_5.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53113.pdf" ]; then
    echo "Restoring: gost-r-53113.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53113.pdf" "/root/qwen/ai_agent/downloads/gost-r-53113.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53114-2008=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-53114-2008=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53114-2008=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-53114-2008=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53114-2008=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-53114-2008=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53114-2008=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-53114-2008=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53114-2008=edt2018.pdf" ]; then
    echo "Restoring: gost-r-53114-2008=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53114-2008=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-53114-2008=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53115-2008=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-53115-2008=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53115-2008=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-53115-2008=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53115-2008=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-53115-2008=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53115-2008=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-53115-2008=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53115-2008=edt2018.pdf" ]; then
    echo "Restoring: gost-r-53115-2008=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53115-2008=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-53115-2008=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53131-2008_1.pdf" ]; then
    echo "Restoring: gost-r-53131-2008_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53131-2008_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-53131-2008_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53131-2008_2.pdf" ]; then
    echo "Restoring: gost-r-53131-2008_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53131-2008_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-53131-2008_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-53131-2008.pdf" ]; then
    echo "Restoring: gost-r-53131-2008.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-53131-2008.pdf" "/root/qwen/ai_agent/downloads/gost-r-53131-2008.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-54581-2011=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-54581-2011=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-54581-2011=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-54581-2011=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-54581-2011=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-54581-2011=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-54581-2011=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-54581-2011=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-54581-2011=edt2018.pdf" ]; then
    echo "Restoring: gost-r-54581-2011=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-54581-2011=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-54581-2011=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-54582-2011=edt2019_1.pdf" ]; then
    echo "Restoring: gost-r-54582-2011=edt2019_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-54582-2011=edt2019_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-54582-2011=edt2019_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-54582-2011=edt2019_2.pdf" ]; then
    echo "Restoring: gost-r-54582-2011=edt2019_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-54582-2011=edt2019_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-54582-2011=edt2019_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-54582-2011=edt2019.pdf" ]; then
    echo "Restoring: gost-r-54582-2011=edt2019.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-54582-2011=edt2019.pdf" "/root/qwen/ai_agent/downloads/gost-r-54582-2011=edt2019.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-54583-2011_1.pdf" ]; then
    echo "Restoring: gost-r-54583-2011_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-54583-2011_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-54583-2011_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-54583-2011_2.pdf" ]; then
    echo "Restoring: gost-r-54583-2011_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-54583-2011_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-54583-2011_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-54583-2011.pdf" ]; then
    echo "Restoring: gost-r-54583-2011.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-54583-2011.pdf" "/root/qwen/ai_agent/downloads/gost-r-54583-2011.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56093-2014=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-56093-2014=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56093-2014=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-56093-2014=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56093-2014=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-56093-2014=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56093-2014=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-56093-2014=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56093-2014=edt2018.pdf" ]; then
    echo "Restoring: gost-r-56093-2014=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56093-2014=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-56093-2014=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56103-2014=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-56103-2014=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56103-2014=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-56103-2014=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56103-2014=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-56103-2014=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56103-2014=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-56103-2014=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56103-2014=edt2018.pdf" ]; then
    echo "Restoring: gost-r-56103-2014=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56103-2014=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-56103-2014=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56115-2014_1.pdf" ]; then
    echo "Restoring: gost-r-56115-2014_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56115-2014_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-56115-2014_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56115-2014_2.pdf" ]; then
    echo "Restoring: gost-r-56115-2014_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56115-2014_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-56115-2014_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56115-2014.pdf" ]; then
    echo "Restoring: gost-r-56115-2014.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56115-2014.pdf" "/root/qwen/ai_agent/downloads/gost-r-56115-2014.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56545-2015=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-56545-2015=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56545-2015=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-56545-2015=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56545-2015=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-56545-2015=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56545-2015=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-56545-2015=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56545-2015=edt2018.pdf" ]; then
    echo "Restoring: gost-r-56545-2015=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56545-2015=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-56545-2015=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56546-2015=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-56546-2015=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56546-2015=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-56546-2015=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56546-2015=edt2018.pdf" ]; then
    echo "Restoring: gost-r-56546-2015=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56546-2015=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-56546-2015=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56938-2016=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-56938-2016=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56938-2016=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-56938-2016=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56938-2016=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-56938-2016=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56938-2016=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-56938-2016=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56938-2016=edt2018.pdf" ]; then
    echo "Restoring: gost-r-56938-2016=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56938-2016=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-56938-2016=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56939-2016=edt2018_1.pdf" ]; then
    echo "Restoring: gost-r-56939-2016=edt2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56939-2016=edt2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-56939-2016=edt2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56939-2016=edt2018_2.pdf" ]; then
    echo "Restoring: gost-r-56939-2016=edt2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56939-2016=edt2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-56939-2016=edt2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-56939-2016=edt2018.pdf" ]; then
    echo "Restoring: gost-r-56939-2016=edt2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-56939-2016=edt2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-56939-2016=edt2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-57628-2017_1.pdf" ]; then
    echo "Restoring: gost-r-57628-2017_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-57628-2017_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-57628-2017_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-57628-2017_2.pdf" ]; then
    echo "Restoring: gost-r-57628-2017_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-57628-2017_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-57628-2017_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-57628-2017.pdf" ]; then
    echo "Restoring: gost-r-57628-2017.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-57628-2017.pdf" "/root/qwen/ai_agent/downloads/gost-r-57628-2017.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58142-2018_1.pdf" ]; then
    echo "Restoring: gost-r-58142-2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58142-2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-58142-2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58142-2018_2.pdf" ]; then
    echo "Restoring: gost-r-58142-2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58142-2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-58142-2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58142-2018.pdf" ]; then
    echo "Restoring: gost-r-58142-2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58142-2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-58142-2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58143-2018_1.pdf" ]; then
    echo "Restoring: gost-r-58143-2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58143-2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-58143-2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58143-2018_2.pdf" ]; then
    echo "Restoring: gost-r-58143-2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58143-2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-58143-2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58143-2018.pdf" ]; then
    echo "Restoring: gost-r-58143-2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58143-2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-58143-2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58256-2018_1.pdf" ]; then
    echo "Restoring: gost-r-58256-2018_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58256-2018_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-58256-2018_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58256-2018_2.pdf" ]; then
    echo "Restoring: gost-r-58256-2018_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58256-2018_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-58256-2018_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58256-2018.pdf" ]; then
    echo "Restoring: gost-r-58256-2018.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58256-2018.pdf" "/root/qwen/ai_agent/downloads/gost-r-58256-2018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58412-2019_1.pdf" ]; then
    echo "Restoring: gost-r-58412-2019_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58412-2019_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-58412-2019_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58412-2019_2.pdf" ]; then
    echo "Restoring: gost-r-58412-2019_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58412-2019_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-58412-2019_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58412-2019.pdf" ]; then
    echo "Restoring: gost-r-58412-2019.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58412-2019.pdf" "/root/qwen/ai_agent/downloads/gost-r-58412-2019.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58833-2020_1.pdf" ]; then
    echo "Restoring: gost-r-58833-2020_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58833-2020_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-58833-2020_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58833-2020_2.pdf" ]; then
    echo "Restoring: gost-r-58833-2020_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58833-2020_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-58833-2020_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-58833-2020.pdf" ]; then
    echo "Restoring: gost-r-58833-2020.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-58833-2020.pdf" "/root/qwen/ai_agent/downloads/gost-r-58833-2020.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59162-2020_1.pdf" ]; then
    echo "Restoring: gost-r-59162-2020_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59162-2020_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-59162-2020_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59162-2020_2.pdf" ]; then
    echo "Restoring: gost-r-59162-2020_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59162-2020_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-59162-2020_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59162-2020.pdf" ]; then
    echo "Restoring: gost-r-59162-2020.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59162-2020.pdf" "/root/qwen/ai_agent/downloads/gost-r-59162-2020.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_10.pdf" ]; then
    echo "Restoring: gost-r-59453_10.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_10.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_10.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_1.pdf" ]; then
    echo "Restoring: gost-r-59453_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_2.pdf" ]; then
    echo "Restoring: gost-r-59453_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_3.pdf" ]; then
    echo "Restoring: gost-r-59453_3.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_3.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_4.pdf" ]; then
    echo "Restoring: gost-r-59453_4.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_4.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_4.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_5.pdf" ]; then
    echo "Restoring: gost-r-59453_5.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_5.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_5.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_6.pdf" ]; then
    echo "Restoring: gost-r-59453_6.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_6.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_6.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_7.pdf" ]; then
    echo "Restoring: gost-r-59453_7.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_7.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_7.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_8.pdf" ]; then
    echo "Restoring: gost-r-59453_8.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_8.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_8.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453_9.pdf" ]; then
    echo "Restoring: gost-r-59453_9.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453_9.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453_9.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59453.pdf" ]; then
    echo "Restoring: gost-r-59453.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59453.pdf" "/root/qwen/ai_agent/downloads/gost-r-59453.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59547-2021_1.pdf" ]; then
    echo "Restoring: gost-r-59547-2021_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59547-2021_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-59547-2021_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59547-2021_2.pdf" ]; then
    echo "Restoring: gost-r-59547-2021_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59547-2021_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-59547-2021_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59547-2021.pdf" ]; then
    echo "Restoring: gost-r-59547-2021.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59547-2021.pdf" "/root/qwen/ai_agent/downloads/gost-r-59547-2021.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59548-2022_1.pdf" ]; then
    echo "Restoring: gost-r-59548-2022_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59548-2022_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-59548-2022_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59548-2022_2.pdf" ]; then
    echo "Restoring: gost-r-59548-2022_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59548-2022_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-59548-2022_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59548-2022.pdf" ]; then
    echo "Restoring: gost-r-59548-2022.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59548-2022.pdf" "/root/qwen/ai_agent/downloads/gost-r-59548-2022.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59709-2022_1.pdf" ]; then
    echo "Restoring: gost-r-59709-2022_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59709-2022_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-59709-2022_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59709-2022_2.pdf" ]; then
    echo "Restoring: gost-r-59709-2022_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59709-2022_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-59709-2022_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59709-2022.pdf" ]; then
    echo "Restoring: gost-r-59709-2022.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59709-2022.pdf" "/root/qwen/ai_agent/downloads/gost-r-59709-2022.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59710-2022_1.pdf" ]; then
    echo "Restoring: gost-r-59710-2022_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59710-2022_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-59710-2022_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59710-2022_2.pdf" ]; then
    echo "Restoring: gost-r-59710-2022_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59710-2022_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-59710-2022_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59710-2022.pdf" ]; then
    echo "Restoring: gost-r-59710-2022.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59710-2022.pdf" "/root/qwen/ai_agent/downloads/gost-r-59710-2022.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59711-2022_1.pdf" ]; then
    echo "Restoring: gost-r-59711-2022_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59711-2022_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-59711-2022_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59711-2022_2.pdf" ]; then
    echo "Restoring: gost-r-59711-2022_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59711-2022_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-59711-2022_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59711-2022.pdf" ]; then
    echo "Restoring: gost-r-59711-2022.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59711-2022.pdf" "/root/qwen/ai_agent/downloads/gost-r-59711-2022.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59712-2022_1.pdf" ]; then
    echo "Restoring: gost-r-59712-2022_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59712-2022_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-59712-2022_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59712-2022_2.pdf" ]; then
    echo "Restoring: gost-r-59712-2022_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59712-2022_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-59712-2022_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-59712-2022.pdf" ]; then
    echo "Restoring: gost-r-59712-2022.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-59712-2022.pdf" "/root/qwen/ai_agent/downloads/gost-r-59712-2022.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-70262_1.pdf" ]; then
    echo "Restoring: gost-r-70262_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-70262_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-70262_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-70262_2.pdf" ]; then
    echo "Restoring: gost-r-70262_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-70262_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-70262_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-70262_3.pdf" ]; then
    echo "Restoring: gost-r-70262_3.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-70262_3.pdf" "/root/qwen/ai_agent/downloads/gost-r-70262_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-70262_4.pdf" ]; then
    echo "Restoring: gost-r-70262_4.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-70262_4.pdf" "/root/qwen/ai_agent/downloads/gost-r-70262_4.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-70262_5.pdf" ]; then
    echo "Restoring: gost-r-70262_5.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-70262_5.pdf" "/root/qwen/ai_agent/downloads/gost-r-70262_5.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-70262.pdf" ]; then
    echo "Restoring: gost-r-70262.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-70262.pdf" "/root/qwen/ai_agent/downloads/gost-r-70262.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71206-2024_1.pdf" ]; then
    echo "Restoring: gost-r-71206-2024_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71206-2024_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-71206-2024_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71206-2024_2.pdf" ]; then
    echo "Restoring: gost-r-71206-2024_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71206-2024_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-71206-2024_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71206-2024.pdf" ]; then
    echo "Restoring: gost-r-71206-2024.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71206-2024.pdf" "/root/qwen/ai_agent/downloads/gost-r-71206-2024.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71207-2024_1.pdf" ]; then
    echo "Restoring: gost-r-71207-2024_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71207-2024_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-71207-2024_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71207-2024_2.pdf" ]; then
    echo "Restoring: gost-r-71207-2024_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71207-2024_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-71207-2024_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71207-2024.pdf" ]; then
    echo "Restoring: gost-r-71207-2024.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71207-2024.pdf" "/root/qwen/ai_agent/downloads/gost-r-71207-2024.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71252-2024_1.pdf" ]; then
    echo "Restoring: gost-r-71252-2024_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71252-2024_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-71252-2024_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71252-2024_2.pdf" ]; then
    echo "Restoring: gost-r-71252-2024_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71252-2024_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-71252-2024_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71252-2024.pdf" ]; then
    echo "Restoring: gost-r-71252-2024.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71252-2024.pdf" "/root/qwen/ai_agent/downloads/gost-r-71252-2024.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71753-2024_1.pdf" ]; then
    echo "Restoring: gost-r-71753-2024_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71753-2024_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-71753-2024_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71753-2024_2.pdf" ]; then
    echo "Restoring: gost-r-71753-2024_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71753-2024_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-71753-2024_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-71753-2024.pdf" ]; then
    echo "Restoring: gost-r-71753-2024.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-71753-2024.pdf" "/root/qwen/ai_agent/downloads/gost-r-71753-2024.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-72118-2025_1.pdf" ]; then
    echo "Restoring: gost-r-72118-2025_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-72118-2025_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-72118-2025_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-72118-2025_2.pdf" ]; then
    echo "Restoring: gost-r-72118-2025_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-72118-2025_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-72118-2025_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-72118-2025.pdf" ]; then
    echo "Restoring: gost-r-72118-2025.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-72118-2025.pdf" "/root/qwen/ai_agent/downloads/gost-r-72118-2025.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-iso-iec-27002-2021_1.pdf" ]; then
    echo "Restoring: gost-r-iso-iec-27002-2021_1.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-iso-iec-27002-2021_1.pdf" "/root/qwen/ai_agent/downloads/gost-r-iso-iec-27002-2021_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-iso-iec-27002-2021_2.pdf" ]; then
    echo "Restoring: gost-r-iso-iec-27002-2021_2.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-iso-iec-27002-2021_2.pdf" "/root/qwen/ai_agent/downloads/gost-r-iso-iec-27002-2021_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/gost-r-iso-iec-27002-2021.pdf" ]; then
    echo "Restoring: gost-r-iso-iec-27002-2021.pdf"
    mv "$SCRIPT_DIR/downloads/gost-r-iso-iec-27002-2021.pdf" "/root/qwen/ai_agent/downloads/gost-r-iso-iec-27002-2021.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/Metodicheskie_rekomendatsii_TSB_RF_1.pdf" ]; then
    echo "Restoring: Metodicheskie_rekomendatsii_TSB_RF_1.pdf"
    mv "$SCRIPT_DIR/downloads/Metodicheskie_rekomendatsii_TSB_RF_1.pdf" "/root/qwen/ai_agent/downloads/Metodicheskie_rekomendatsii_TSB_RF_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/Metodicheskie_rekomendatsii_TSB_RF.pdf" ]; then
    echo "Restoring: Metodicheskie_rekomendatsii_TSB_RF.pdf"
    mv "$SCRIPT_DIR/downloads/Metodicheskie_rekomendatsii_TSB_RF.pdf" "/root/qwen/ai_agent/downloads/Metodicheskie_rekomendatsii_TSB_RF.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_1.pdf" ]; then
    echo "Restoring: PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_1.pdf"
    mv "$SCRIPT_DIR/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_1.pdf" "/root/qwen/ai_agent/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_2.pdf" ]; then
    echo "Restoring: PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_2.pdf"
    mv "$SCRIPT_DIR/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_2.pdf" "/root/qwen/ai_agent/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_3.pdf" ]; then
    echo "Restoring: PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_3.pdf"
    mv "$SCRIPT_DIR/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_3.pdf" "/root/qwen/ai_agent/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0.pdf" ]; then
    echo "Restoring: PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0.pdf"
    mv "$SCRIPT_DIR/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0.pdf" "/root/qwen/ai_agent/downloads/PCI_Mobile_Payment_Acceptance_Security_Guidelines_for_Developers_v2_0.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/politika-informatsionnoy-bezopasnosti_1.pdf" ]; then
    echo "Restoring: politika-informatsionnoy-bezopasnosti_1.pdf"
    mv "$SCRIPT_DIR/downloads/politika-informatsionnoy-bezopasnosti_1.pdf" "/root/qwen/ai_agent/downloads/politika-informatsionnoy-bezopasnosti_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/politika-informatsionnoy-bezopasnosti_2.pdf" ]; then
    echo "Restoring: politika-informatsionnoy-bezopasnosti_2.pdf"
    mv "$SCRIPT_DIR/downloads/politika-informatsionnoy-bezopasnosti_2.pdf" "/root/qwen/ai_agent/downloads/politika-informatsionnoy-bezopasnosti_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/politika-informatsionnoy-bezopasnosti.pdf" ]; then
    echo "Restoring: politika-informatsionnoy-bezopasnosti.pdf"
    mv "$SCRIPT_DIR/downloads/politika-informatsionnoy-bezopasnosti.pdf" "/root/qwen/ai_agent/downloads/politika-informatsionnoy-bezopasnosti.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1-1323565.1_1.pdf" ]; then
    echo "Restoring: r-1-1323565.1_1.pdf"
    mv "$SCRIPT_DIR/downloads/r-1-1323565.1_1.pdf" "/root/qwen/ai_agent/downloads/r-1-1323565.1_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1-1323565.1_2.pdf" ]; then
    echo "Restoring: r-1-1323565.1_2.pdf"
    mv "$SCRIPT_DIR/downloads/r-1-1323565.1_2.pdf" "/root/qwen/ai_agent/downloads/r-1-1323565.1_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1-1323565.1.pdf" ]; then
    echo "Restoring: r-1-1323565.1.pdf"
    mv "$SCRIPT_DIR/downloads/r-1-1323565.1.pdf" "/root/qwen/ai_agent/downloads/r-1-1323565.1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_10.pdf" ]; then
    echo "Restoring: r-1323565.1_10.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_10.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_10.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_11.pdf" ]; then
    echo "Restoring: r-1323565.1_11.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_11.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_11.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_12.pdf" ]; then
    echo "Restoring: r-1323565.1_12.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_12.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_12.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_13.pdf" ]; then
    echo "Restoring: r-1323565.1_13.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_13.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_13.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_14.pdf" ]; then
    echo "Restoring: r-1323565.1_14.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_14.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_14.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_15.pdf" ]; then
    echo "Restoring: r-1323565.1_15.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_15.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_15.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_16.pdf" ]; then
    echo "Restoring: r-1323565.1_16.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_16.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_16.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_17.pdf" ]; then
    echo "Restoring: r-1323565.1_17.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_17.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_17.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_18.pdf" ]; then
    echo "Restoring: r-1323565.1_18.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_18.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_18.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_19.pdf" ]; then
    echo "Restoring: r-1323565.1_19.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_19.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_19.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_1.pdf" ]; then
    echo "Restoring: r-1323565.1_1.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_1.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_20.pdf" ]; then
    echo "Restoring: r-1323565.1_20.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_20.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_20.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_21.pdf" ]; then
    echo "Restoring: r-1323565.1_21.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_21.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_21.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_22.pdf" ]; then
    echo "Restoring: r-1323565.1_22.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_22.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_22.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_23.pdf" ]; then
    echo "Restoring: r-1323565.1_23.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_23.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_23.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_24.pdf" ]; then
    echo "Restoring: r-1323565.1_24.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_24.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_24.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_25.pdf" ]; then
    echo "Restoring: r-1323565.1_25.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_25.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_25.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_26.pdf" ]; then
    echo "Restoring: r-1323565.1_26.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_26.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_26.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_27.pdf" ]; then
    echo "Restoring: r-1323565.1_27.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_27.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_27.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_28.pdf" ]; then
    echo "Restoring: r-1323565.1_28.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_28.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_28.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_29.pdf" ]; then
    echo "Restoring: r-1323565.1_29.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_29.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_29.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_2.pdf" ]; then
    echo "Restoring: r-1323565.1_2.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_2.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_30.pdf" ]; then
    echo "Restoring: r-1323565.1_30.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_30.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_30.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_31.pdf" ]; then
    echo "Restoring: r-1323565.1_31.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_31.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_31.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_32.pdf" ]; then
    echo "Restoring: r-1323565.1_32.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_32.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_32.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_33.pdf" ]; then
    echo "Restoring: r-1323565.1_33.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_33.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_33.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_34.pdf" ]; then
    echo "Restoring: r-1323565.1_34.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_34.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_34.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_35.pdf" ]; then
    echo "Restoring: r-1323565.1_35.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_35.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_35.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_36.pdf" ]; then
    echo "Restoring: r-1323565.1_36.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_36.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_36.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_37.pdf" ]; then
    echo "Restoring: r-1323565.1_37.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_37.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_37.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_38.pdf" ]; then
    echo "Restoring: r-1323565.1_38.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_38.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_38.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_39.pdf" ]; then
    echo "Restoring: r-1323565.1_39.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_39.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_39.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_3.pdf" ]; then
    echo "Restoring: r-1323565.1_3.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_3.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_40.pdf" ]; then
    echo "Restoring: r-1323565.1_40.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_40.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_40.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_41.pdf" ]; then
    echo "Restoring: r-1323565.1_41.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_41.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_41.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_42.pdf" ]; then
    echo "Restoring: r-1323565.1_42.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_42.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_42.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_43.pdf" ]; then
    echo "Restoring: r-1323565.1_43.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_43.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_43.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_44.pdf" ]; then
    echo "Restoring: r-1323565.1_44.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_44.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_44.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_45.pdf" ]; then
    echo "Restoring: r-1323565.1_45.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_45.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_45.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_46.pdf" ]; then
    echo "Restoring: r-1323565.1_46.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_46.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_46.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_47.pdf" ]; then
    echo "Restoring: r-1323565.1_47.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_47.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_47.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_48.pdf" ]; then
    echo "Restoring: r-1323565.1_48.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_48.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_48.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_49.pdf" ]; then
    echo "Restoring: r-1323565.1_49.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_49.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_49.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_4.pdf" ]; then
    echo "Restoring: r-1323565.1_4.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_4.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_4.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_50.pdf" ]; then
    echo "Restoring: r-1323565.1_50.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_50.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_50.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_51.pdf" ]; then
    echo "Restoring: r-1323565.1_51.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_51.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_51.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_52.pdf" ]; then
    echo "Restoring: r-1323565.1_52.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_52.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_52.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_53.pdf" ]; then
    echo "Restoring: r-1323565.1_53.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_53.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_53.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_54.pdf" ]; then
    echo "Restoring: r-1323565.1_54.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_54.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_54.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_55.pdf" ]; then
    echo "Restoring: r-1323565.1_55.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_55.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_55.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_56.pdf" ]; then
    echo "Restoring: r-1323565.1_56.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_56.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_56.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_57.pdf" ]; then
    echo "Restoring: r-1323565.1_57.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_57.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_57.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_58.pdf" ]; then
    echo "Restoring: r-1323565.1_58.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_58.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_58.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_5.pdf" ]; then
    echo "Restoring: r-1323565.1_5.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_5.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_5.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_6.pdf" ]; then
    echo "Restoring: r-1323565.1_6.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_6.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_6.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_7.pdf" ]; then
    echo "Restoring: r-1323565.1_7.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_7.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_7.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_8.pdf" ]; then
    echo "Restoring: r-1323565.1_8.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_8.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_8.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1_9.pdf" ]; then
    echo "Restoring: r-1323565.1_9.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1_9.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1_9.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-1323565.1.pdf" ]; then
    echo "Restoring: r-1323565.1.pdf"
    mv "$SCRIPT_DIR/downloads/r-1323565.1.pdf" "/root/qwen/ai_agent/downloads/r-1323565.1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_10.pdf" ]; then
    echo "Restoring: r-50.1_10.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_10.pdf" "/root/qwen/ai_agent/downloads/r-50.1_10.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_11.pdf" ]; then
    echo "Restoring: r-50.1_11.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_11.pdf" "/root/qwen/ai_agent/downloads/r-50.1_11.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_12.pdf" ]; then
    echo "Restoring: r-50.1_12.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_12.pdf" "/root/qwen/ai_agent/downloads/r-50.1_12.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_13.pdf" ]; then
    echo "Restoring: r-50.1_13.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_13.pdf" "/root/qwen/ai_agent/downloads/r-50.1_13.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_14.pdf" ]; then
    echo "Restoring: r-50.1_14.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_14.pdf" "/root/qwen/ai_agent/downloads/r-50.1_14.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_15.pdf" ]; then
    echo "Restoring: r-50.1_15.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_15.pdf" "/root/qwen/ai_agent/downloads/r-50.1_15.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_1.pdf" ]; then
    echo "Restoring: r-50.1_1.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_1.pdf" "/root/qwen/ai_agent/downloads/r-50.1_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_2.pdf" ]; then
    echo "Restoring: r-50.1_2.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_2.pdf" "/root/qwen/ai_agent/downloads/r-50.1_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_3.pdf" ]; then
    echo "Restoring: r-50.1_3.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_3.pdf" "/root/qwen/ai_agent/downloads/r-50.1_3.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_4.pdf" ]; then
    echo "Restoring: r-50.1_4.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_4.pdf" "/root/qwen/ai_agent/downloads/r-50.1_4.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_5.pdf" ]; then
    echo "Restoring: r-50.1_5.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_5.pdf" "/root/qwen/ai_agent/downloads/r-50.1_5.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_6.pdf" ]; then
    echo "Restoring: r-50.1_6.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_6.pdf" "/root/qwen/ai_agent/downloads/r-50.1_6.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_7.pdf" ]; then
    echo "Restoring: r-50.1_7.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_7.pdf" "/root/qwen/ai_agent/downloads/r-50.1_7.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_8.pdf" ]; then
    echo "Restoring: r-50.1_8.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_8.pdf" "/root/qwen/ai_agent/downloads/r-50.1_8.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1_9.pdf" ]; then
    echo "Restoring: r-50.1_9.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1_9.pdf" "/root/qwen/ai_agent/downloads/r-50.1_9.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/r-50.1.pdf" ]; then
    echo "Restoring: r-50.1.pdf"
    mv "$SCRIPT_DIR/downloads/r-50.1.pdf" "/root/qwen/ai_agent/downloads/r-50.1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/Securing-Mobile-Applications-and-Devices-%5BCIO-IT-Security-12-67-Rev-7%5D-10-01-2024_1.pdf" ]; then
    echo "Restoring: Securing-Mobile-Applications-and-Devices-%5BCIO-IT-Security-12-67-Rev-7%5D-10-01-2024_1.pdf"
    mv "$SCRIPT_DIR/downloads/Securing-Mobile-Applications-and-Devices-%5BCIO-IT-Security-12-67-Rev-7%5D-10-01-2024_1.pdf" "/root/qwen/ai_agent/downloads/Securing-Mobile-Applications-and-Devices-%5BCIO-IT-Security-12-67-Rev-7%5D-10-01-2024_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/Securing-Mobile-Applications-and-Devices-%5BCIO-IT-Security-12-67-Rev-7%5D-10-01-2024.pdf" ]; then
    echo "Restoring: Securing-Mobile-Applications-and-Devices-%5BCIO-IT-Security-12-67-Rev-7%5D-10-01-2024.pdf"
    mv "$SCRIPT_DIR/downloads/Securing-Mobile-Applications-and-Devices-%5BCIO-IT-Security-12-67-Rev-7%5D-10-01-2024.pdf" "/root/qwen/ai_agent/downloads/Securing-Mobile-Applications-and-Devices-%5BCIO-IT-Security-12-67-Rev-7%5D-10-01-2024.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/T10-p15_1.pdf" ]; then
    echo "Restoring: T10-p15_1.pdf"
    mv "$SCRIPT_DIR/downloads/T10-p15_1.pdf" "/root/qwen/ai_agent/downloads/T10-p15_1.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/T10-p15_2.pdf" ]; then
    echo "Restoring: T10-p15_2.pdf"
    mv "$SCRIPT_DIR/downloads/T10-p15_2.pdf" "/root/qwen/ai_agent/downloads/T10-p15_2.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/T10-p15.pdf" ]; then
    echo "Restoring: T10-p15.pdf"
    mv "$SCRIPT_DIR/downloads/T10-p15.pdf" "/root/qwen/ai_agent/downloads/T10-p15.pdf"
fi


echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Recovery complete!"
echo "═══════════════════════════════════════════════════════════════"
