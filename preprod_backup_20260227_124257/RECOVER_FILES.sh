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

if [ -f "$SCRIPT_DIR/downloads/doc_216.pdf" ]; then
    echo "Restoring: doc_216.pdf"
    mv "$SCRIPT_DIR/downloads/doc_216.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_216.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_248.pdf" ]; then
    echo "Restoring: doc_248.pdf"
    mv "$SCRIPT_DIR/downloads/doc_248.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_248.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_094.pdf" ]; then
    echo "Restoring: doc_094.pdf"
    mv "$SCRIPT_DIR/downloads/doc_094.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_094.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_045.pdf" ]; then
    echo "Restoring: doc_045.pdf"
    mv "$SCRIPT_DIR/downloads/doc_045.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_045.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_055.pdf" ]; then
    echo "Restoring: doc_055.pdf"
    mv "$SCRIPT_DIR/downloads/doc_055.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_055.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_048.pdf" ]; then
    echo "Restoring: doc_048.pdf"
    mv "$SCRIPT_DIR/downloads/doc_048.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_048.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_005.pdf" ]; then
    echo "Restoring: doc_005.pdf"
    mv "$SCRIPT_DIR/downloads/doc_005.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_005.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_181.pdf" ]; then
    echo "Restoring: doc_181.pdf"
    mv "$SCRIPT_DIR/downloads/doc_181.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_181.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_240.pdf" ]; then
    echo "Restoring: doc_240.pdf"
    mv "$SCRIPT_DIR/downloads/doc_240.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_240.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_036.pdf" ]; then
    echo "Restoring: doc_036.pdf"
    mv "$SCRIPT_DIR/downloads/doc_036.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_036.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_114.pdf" ]; then
    echo "Restoring: doc_114.pdf"
    mv "$SCRIPT_DIR/downloads/doc_114.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_114.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_119.pdf" ]; then
    echo "Restoring: doc_119.pdf"
    mv "$SCRIPT_DIR/downloads/doc_119.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_119.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_291.pdf" ]; then
    echo "Restoring: doc_291.pdf"
    mv "$SCRIPT_DIR/downloads/doc_291.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_291.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_191.pdf" ]; then
    echo "Restoring: doc_191.pdf"
    mv "$SCRIPT_DIR/downloads/doc_191.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_191.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_178.pdf" ]; then
    echo "Restoring: doc_178.pdf"
    mv "$SCRIPT_DIR/downloads/doc_178.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_178.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_225.pdf" ]; then
    echo "Restoring: doc_225.pdf"
    mv "$SCRIPT_DIR/downloads/doc_225.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_225.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_233.pdf" ]; then
    echo "Restoring: doc_233.pdf"
    mv "$SCRIPT_DIR/downloads/doc_233.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_233.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_081.pdf" ]; then
    echo "Restoring: doc_081.pdf"
    mv "$SCRIPT_DIR/downloads/doc_081.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_081.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_064.pdf" ]; then
    echo "Restoring: doc_064.pdf"
    mv "$SCRIPT_DIR/downloads/doc_064.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_064.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_176.pdf" ]; then
    echo "Restoring: doc_176.pdf"
    mv "$SCRIPT_DIR/downloads/doc_176.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_176.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_261.pdf" ]; then
    echo "Restoring: doc_261.pdf"
    mv "$SCRIPT_DIR/downloads/doc_261.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_261.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_273.pdf" ]; then
    echo "Restoring: doc_273.pdf"
    mv "$SCRIPT_DIR/downloads/doc_273.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_273.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_220.pdf" ]; then
    echo "Restoring: doc_220.pdf"
    mv "$SCRIPT_DIR/downloads/doc_220.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_220.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_006.pdf" ]; then
    echo "Restoring: doc_006.pdf"
    mv "$SCRIPT_DIR/downloads/doc_006.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_006.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_208.pdf" ]; then
    echo "Restoring: doc_208.pdf"
    mv "$SCRIPT_DIR/downloads/doc_208.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_208.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_185.pdf" ]; then
    echo "Restoring: doc_185.pdf"
    mv "$SCRIPT_DIR/downloads/doc_185.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_185.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_172.pdf" ]; then
    echo "Restoring: doc_172.pdf"
    mv "$SCRIPT_DIR/downloads/doc_172.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_172.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_179.pdf" ]; then
    echo "Restoring: doc_179.pdf"
    mv "$SCRIPT_DIR/downloads/doc_179.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_179.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_245.pdf" ]; then
    echo "Restoring: doc_245.pdf"
    mv "$SCRIPT_DIR/downloads/doc_245.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_245.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_260.pdf" ]; then
    echo "Restoring: doc_260.pdf"
    mv "$SCRIPT_DIR/downloads/doc_260.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_260.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_138.pdf" ]; then
    echo "Restoring: doc_138.pdf"
    mv "$SCRIPT_DIR/downloads/doc_138.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_138.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_168.pdf" ]; then
    echo "Restoring: doc_168.pdf"
    mv "$SCRIPT_DIR/downloads/doc_168.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_168.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_128.pdf" ]; then
    echo "Restoring: doc_128.pdf"
    mv "$SCRIPT_DIR/downloads/doc_128.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_128.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_160.pdf" ]; then
    echo "Restoring: doc_160.pdf"
    mv "$SCRIPT_DIR/downloads/doc_160.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_160.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_091.pdf" ]; then
    echo "Restoring: doc_091.pdf"
    mv "$SCRIPT_DIR/downloads/doc_091.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_091.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_037.pdf" ]; then
    echo "Restoring: doc_037.pdf"
    mv "$SCRIPT_DIR/downloads/doc_037.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_037.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_157.pdf" ]; then
    echo "Restoring: doc_157.pdf"
    mv "$SCRIPT_DIR/downloads/doc_157.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_157.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_129.pdf" ]; then
    echo "Restoring: doc_129.pdf"
    mv "$SCRIPT_DIR/downloads/doc_129.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_129.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_192.pdf" ]; then
    echo "Restoring: doc_192.pdf"
    mv "$SCRIPT_DIR/downloads/doc_192.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_192.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_140.pdf" ]; then
    echo "Restoring: doc_140.pdf"
    mv "$SCRIPT_DIR/downloads/doc_140.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_140.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_218.pdf" ]; then
    echo "Restoring: doc_218.pdf"
    mv "$SCRIPT_DIR/downloads/doc_218.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_218.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_213.pdf" ]; then
    echo "Restoring: doc_213.pdf"
    mv "$SCRIPT_DIR/downloads/doc_213.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_213.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_002.pdf" ]; then
    echo "Restoring: doc_002.pdf"
    mv "$SCRIPT_DIR/downloads/doc_002.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_002.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_252.pdf" ]; then
    echo "Restoring: doc_252.pdf"
    mv "$SCRIPT_DIR/downloads/doc_252.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_252.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_230.pdf" ]; then
    echo "Restoring: doc_230.pdf"
    mv "$SCRIPT_DIR/downloads/doc_230.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_230.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_212.pdf" ]; then
    echo "Restoring: doc_212.pdf"
    mv "$SCRIPT_DIR/downloads/doc_212.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_212.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_082.pdf" ]; then
    echo "Restoring: doc_082.pdf"
    mv "$SCRIPT_DIR/downloads/doc_082.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_082.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_271.pdf" ]; then
    echo "Restoring: doc_271.pdf"
    mv "$SCRIPT_DIR/downloads/doc_271.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_271.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_079.pdf" ]; then
    echo "Restoring: doc_079.pdf"
    mv "$SCRIPT_DIR/downloads/doc_079.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_079.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_030.pdf" ]; then
    echo "Restoring: doc_030.pdf"
    mv "$SCRIPT_DIR/downloads/doc_030.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_030.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_175.pdf" ]; then
    echo "Restoring: doc_175.pdf"
    mv "$SCRIPT_DIR/downloads/doc_175.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_175.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_050.pdf" ]; then
    echo "Restoring: doc_050.pdf"
    mv "$SCRIPT_DIR/downloads/doc_050.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_050.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_244.pdf" ]; then
    echo "Restoring: doc_244.pdf"
    mv "$SCRIPT_DIR/downloads/doc_244.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_244.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_295.pdf" ]; then
    echo "Restoring: doc_295.pdf"
    mv "$SCRIPT_DIR/downloads/doc_295.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_295.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_201.pdf" ]; then
    echo "Restoring: doc_201.pdf"
    mv "$SCRIPT_DIR/downloads/doc_201.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_201.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_083.pdf" ]; then
    echo "Restoring: doc_083.pdf"
    mv "$SCRIPT_DIR/downloads/doc_083.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_083.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_293.pdf" ]; then
    echo "Restoring: doc_293.pdf"
    mv "$SCRIPT_DIR/downloads/doc_293.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_293.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_078.pdf" ]; then
    echo "Restoring: doc_078.pdf"
    mv "$SCRIPT_DIR/downloads/doc_078.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_078.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_117.pdf" ]; then
    echo "Restoring: doc_117.pdf"
    mv "$SCRIPT_DIR/downloads/doc_117.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_117.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_136.pdf" ]; then
    echo "Restoring: doc_136.pdf"
    mv "$SCRIPT_DIR/downloads/doc_136.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_136.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_015.pdf" ]; then
    echo "Restoring: doc_015.pdf"
    mv "$SCRIPT_DIR/downloads/doc_015.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_015.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_106.pdf" ]; then
    echo "Restoring: doc_106.pdf"
    mv "$SCRIPT_DIR/downloads/doc_106.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_106.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_113.pdf" ]; then
    echo "Restoring: doc_113.pdf"
    mv "$SCRIPT_DIR/downloads/doc_113.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_113.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_070.pdf" ]; then
    echo "Restoring: doc_070.pdf"
    mv "$SCRIPT_DIR/downloads/doc_070.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_070.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_278.pdf" ]; then
    echo "Restoring: doc_278.pdf"
    mv "$SCRIPT_DIR/downloads/doc_278.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_278.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_116.pdf" ]; then
    echo "Restoring: doc_116.pdf"
    mv "$SCRIPT_DIR/downloads/doc_116.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_116.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_024.pdf" ]; then
    echo "Restoring: doc_024.pdf"
    mv "$SCRIPT_DIR/downloads/doc_024.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_024.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_209.pdf" ]; then
    echo "Restoring: doc_209.pdf"
    mv "$SCRIPT_DIR/downloads/doc_209.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_209.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_111.pdf" ]; then
    echo "Restoring: doc_111.pdf"
    mv "$SCRIPT_DIR/downloads/doc_111.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_111.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_217.pdf" ]; then
    echo "Restoring: doc_217.pdf"
    mv "$SCRIPT_DIR/downloads/doc_217.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_217.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_022.pdf" ]; then
    echo "Restoring: doc_022.pdf"
    mv "$SCRIPT_DIR/downloads/doc_022.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_022.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_257.pdf" ]; then
    echo "Restoring: doc_257.pdf"
    mv "$SCRIPT_DIR/downloads/doc_257.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_257.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_067.pdf" ]; then
    echo "Restoring: doc_067.pdf"
    mv "$SCRIPT_DIR/downloads/doc_067.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_067.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_011.pdf" ]; then
    echo "Restoring: doc_011.pdf"
    mv "$SCRIPT_DIR/downloads/doc_011.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_011.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_072.pdf" ]; then
    echo "Restoring: doc_072.pdf"
    mv "$SCRIPT_DIR/downloads/doc_072.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_072.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_242.pdf" ]; then
    echo "Restoring: doc_242.pdf"
    mv "$SCRIPT_DIR/downloads/doc_242.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_242.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_032.pdf" ]; then
    echo "Restoring: doc_032.pdf"
    mv "$SCRIPT_DIR/downloads/doc_032.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_032.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_017.pdf" ]; then
    echo "Restoring: doc_017.pdf"
    mv "$SCRIPT_DIR/downloads/doc_017.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_017.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_044.pdf" ]; then
    echo "Restoring: doc_044.pdf"
    mv "$SCRIPT_DIR/downloads/doc_044.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_044.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_039.pdf" ]; then
    echo "Restoring: doc_039.pdf"
    mv "$SCRIPT_DIR/downloads/doc_039.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_039.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_276.pdf" ]; then
    echo "Restoring: doc_276.pdf"
    mv "$SCRIPT_DIR/downloads/doc_276.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_276.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_061.pdf" ]; then
    echo "Restoring: doc_061.pdf"
    mv "$SCRIPT_DIR/downloads/doc_061.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_061.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_101.pdf" ]; then
    echo "Restoring: doc_101.pdf"
    mv "$SCRIPT_DIR/downloads/doc_101.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_101.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_234.pdf" ]; then
    echo "Restoring: doc_234.pdf"
    mv "$SCRIPT_DIR/downloads/doc_234.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_234.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_269.pdf" ]; then
    echo "Restoring: doc_269.pdf"
    mv "$SCRIPT_DIR/downloads/doc_269.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_269.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_274.pdf" ]; then
    echo "Restoring: doc_274.pdf"
    mv "$SCRIPT_DIR/downloads/doc_274.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_274.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_141.pdf" ]; then
    echo "Restoring: doc_141.pdf"
    mv "$SCRIPT_DIR/downloads/doc_141.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_141.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_275.pdf" ]; then
    echo "Restoring: doc_275.pdf"
    mv "$SCRIPT_DIR/downloads/doc_275.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_275.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_251.pdf" ]; then
    echo "Restoring: doc_251.pdf"
    mv "$SCRIPT_DIR/downloads/doc_251.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_251.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_170.pdf" ]; then
    echo "Restoring: doc_170.pdf"
    mv "$SCRIPT_DIR/downloads/doc_170.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_170.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_193.pdf" ]; then
    echo "Restoring: doc_193.pdf"
    mv "$SCRIPT_DIR/downloads/doc_193.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_193.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_099.pdf" ]; then
    echo "Restoring: doc_099.pdf"
    mv "$SCRIPT_DIR/downloads/doc_099.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_099.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_010.pdf" ]; then
    echo "Restoring: doc_010.pdf"
    mv "$SCRIPT_DIR/downloads/doc_010.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_010.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_239.pdf" ]; then
    echo "Restoring: doc_239.pdf"
    mv "$SCRIPT_DIR/downloads/doc_239.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_239.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_155.pdf" ]; then
    echo "Restoring: doc_155.pdf"
    mv "$SCRIPT_DIR/downloads/doc_155.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_155.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_164.pdf" ]; then
    echo "Restoring: doc_164.pdf"
    mv "$SCRIPT_DIR/downloads/doc_164.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_164.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_264.pdf" ]; then
    echo "Restoring: doc_264.pdf"
    mv "$SCRIPT_DIR/downloads/doc_264.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_264.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_018.pdf" ]; then
    echo "Restoring: doc_018.pdf"
    mv "$SCRIPT_DIR/downloads/doc_018.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_018.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_146.pdf" ]; then
    echo "Restoring: doc_146.pdf"
    mv "$SCRIPT_DIR/downloads/doc_146.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_146.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_125.pdf" ]; then
    echo "Restoring: doc_125.pdf"
    mv "$SCRIPT_DIR/downloads/doc_125.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_125.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_241.pdf" ]; then
    echo "Restoring: doc_241.pdf"
    mv "$SCRIPT_DIR/downloads/doc_241.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_241.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_063.pdf" ]; then
    echo "Restoring: doc_063.pdf"
    mv "$SCRIPT_DIR/downloads/doc_063.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_063.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_202.pdf" ]; then
    echo "Restoring: doc_202.pdf"
    mv "$SCRIPT_DIR/downloads/doc_202.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_202.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_135.pdf" ]; then
    echo "Restoring: doc_135.pdf"
    mv "$SCRIPT_DIR/downloads/doc_135.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_135.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_154.pdf" ]; then
    echo "Restoring: doc_154.pdf"
    mv "$SCRIPT_DIR/downloads/doc_154.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_154.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_144.pdf" ]; then
    echo "Restoring: doc_144.pdf"
    mv "$SCRIPT_DIR/downloads/doc_144.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_144.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_292.pdf" ]; then
    echo "Restoring: doc_292.pdf"
    mv "$SCRIPT_DIR/downloads/doc_292.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_292.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_143.pdf" ]; then
    echo "Restoring: doc_143.pdf"
    mv "$SCRIPT_DIR/downloads/doc_143.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_143.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_156.pdf" ]; then
    echo "Restoring: doc_156.pdf"
    mv "$SCRIPT_DIR/downloads/doc_156.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_156.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_222.pdf" ]; then
    echo "Restoring: doc_222.pdf"
    mv "$SCRIPT_DIR/downloads/doc_222.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_222.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_279.pdf" ]; then
    echo "Restoring: doc_279.pdf"
    mv "$SCRIPT_DIR/downloads/doc_279.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_279.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_060.pdf" ]; then
    echo "Restoring: doc_060.pdf"
    mv "$SCRIPT_DIR/downloads/doc_060.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_060.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_054.pdf" ]; then
    echo "Restoring: doc_054.pdf"
    mv "$SCRIPT_DIR/downloads/doc_054.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_054.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_028.pdf" ]; then
    echo "Restoring: doc_028.pdf"
    mv "$SCRIPT_DIR/downloads/doc_028.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_028.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_026.pdf" ]; then
    echo "Restoring: doc_026.pdf"
    mv "$SCRIPT_DIR/downloads/doc_026.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_026.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_215.pdf" ]; then
    echo "Restoring: doc_215.pdf"
    mv "$SCRIPT_DIR/downloads/doc_215.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_215.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_221.pdf" ]; then
    echo "Restoring: doc_221.pdf"
    mv "$SCRIPT_DIR/downloads/doc_221.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_221.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_133.pdf" ]; then
    echo "Restoring: doc_133.pdf"
    mv "$SCRIPT_DIR/downloads/doc_133.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_133.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_149.pdf" ]; then
    echo "Restoring: doc_149.pdf"
    mv "$SCRIPT_DIR/downloads/doc_149.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_149.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_052.pdf" ]; then
    echo "Restoring: doc_052.pdf"
    mv "$SCRIPT_DIR/downloads/doc_052.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_052.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_092.pdf" ]; then
    echo "Restoring: doc_092.pdf"
    mv "$SCRIPT_DIR/downloads/doc_092.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_092.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_180.pdf" ]; then
    echo "Restoring: doc_180.pdf"
    mv "$SCRIPT_DIR/downloads/doc_180.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_180.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_167.pdf" ]; then
    echo "Restoring: doc_167.pdf"
    mv "$SCRIPT_DIR/downloads/doc_167.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_167.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_112.pdf" ]; then
    echo "Restoring: doc_112.pdf"
    mv "$SCRIPT_DIR/downloads/doc_112.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_112.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_151.pdf" ]; then
    echo "Restoring: doc_151.pdf"
    mv "$SCRIPT_DIR/downloads/doc_151.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_151.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_250.pdf" ]; then
    echo "Restoring: doc_250.pdf"
    mv "$SCRIPT_DIR/downloads/doc_250.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_250.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_159.pdf" ]; then
    echo "Restoring: doc_159.pdf"
    mv "$SCRIPT_DIR/downloads/doc_159.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_159.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_137.pdf" ]; then
    echo "Restoring: doc_137.pdf"
    mv "$SCRIPT_DIR/downloads/doc_137.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_137.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_285.pdf" ]; then
    echo "Restoring: doc_285.pdf"
    mv "$SCRIPT_DIR/downloads/doc_285.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_285.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_283.pdf" ]; then
    echo "Restoring: doc_283.pdf"
    mv "$SCRIPT_DIR/downloads/doc_283.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_283.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_108.pdf" ]; then
    echo "Restoring: doc_108.pdf"
    mv "$SCRIPT_DIR/downloads/doc_108.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_108.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_097.pdf" ]; then
    echo "Restoring: doc_097.pdf"
    mv "$SCRIPT_DIR/downloads/doc_097.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_097.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_189.pdf" ]; then
    echo "Restoring: doc_189.pdf"
    mv "$SCRIPT_DIR/downloads/doc_189.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_189.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_110.pdf" ]; then
    echo "Restoring: doc_110.pdf"
    mv "$SCRIPT_DIR/downloads/doc_110.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_110.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_004.pdf" ]; then
    echo "Restoring: doc_004.pdf"
    mv "$SCRIPT_DIR/downloads/doc_004.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_004.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_031.pdf" ]; then
    echo "Restoring: doc_031.pdf"
    mv "$SCRIPT_DIR/downloads/doc_031.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_031.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_056.pdf" ]; then
    echo "Restoring: doc_056.pdf"
    mv "$SCRIPT_DIR/downloads/doc_056.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_056.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_109.pdf" ]; then
    echo "Restoring: doc_109.pdf"
    mv "$SCRIPT_DIR/downloads/doc_109.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_109.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_265.pdf" ]; then
    echo "Restoring: doc_265.pdf"
    mv "$SCRIPT_DIR/downloads/doc_265.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_265.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_277.pdf" ]; then
    echo "Restoring: doc_277.pdf"
    mv "$SCRIPT_DIR/downloads/doc_277.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_277.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_033.pdf" ]; then
    echo "Restoring: doc_033.pdf"
    mv "$SCRIPT_DIR/downloads/doc_033.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_033.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_088.pdf" ]; then
    echo "Restoring: doc_088.pdf"
    mv "$SCRIPT_DIR/downloads/doc_088.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_088.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_105.pdf" ]; then
    echo "Restoring: doc_105.pdf"
    mv "$SCRIPT_DIR/downloads/doc_105.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_105.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_165.pdf" ]; then
    echo "Restoring: doc_165.pdf"
    mv "$SCRIPT_DIR/downloads/doc_165.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_165.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_089.pdf" ]; then
    echo "Restoring: doc_089.pdf"
    mv "$SCRIPT_DIR/downloads/doc_089.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_089.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_237.pdf" ]; then
    echo "Restoring: doc_237.pdf"
    mv "$SCRIPT_DIR/downloads/doc_237.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_237.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_259.pdf" ]; then
    echo "Restoring: doc_259.pdf"
    mv "$SCRIPT_DIR/downloads/doc_259.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_259.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_258.pdf" ]; then
    echo "Restoring: doc_258.pdf"
    mv "$SCRIPT_DIR/downloads/doc_258.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_258.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_069.pdf" ]; then
    echo "Restoring: doc_069.pdf"
    mv "$SCRIPT_DIR/downloads/doc_069.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_069.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_122.pdf" ]; then
    echo "Restoring: doc_122.pdf"
    mv "$SCRIPT_DIR/downloads/doc_122.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_122.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_195.pdf" ]; then
    echo "Restoring: doc_195.pdf"
    mv "$SCRIPT_DIR/downloads/doc_195.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_195.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_177.pdf" ]; then
    echo "Restoring: doc_177.pdf"
    mv "$SCRIPT_DIR/downloads/doc_177.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_177.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_051.pdf" ]; then
    echo "Restoring: doc_051.pdf"
    mv "$SCRIPT_DIR/downloads/doc_051.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_051.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_073.pdf" ]; then
    echo "Restoring: doc_073.pdf"
    mv "$SCRIPT_DIR/downloads/doc_073.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_073.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_003.pdf" ]; then
    echo "Restoring: doc_003.pdf"
    mv "$SCRIPT_DIR/downloads/doc_003.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_003.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_059.pdf" ]; then
    echo "Restoring: doc_059.pdf"
    mv "$SCRIPT_DIR/downloads/doc_059.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_059.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_194.pdf" ]; then
    echo "Restoring: doc_194.pdf"
    mv "$SCRIPT_DIR/downloads/doc_194.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_194.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_077.pdf" ]; then
    echo "Restoring: doc_077.pdf"
    mv "$SCRIPT_DIR/downloads/doc_077.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_077.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_087.pdf" ]; then
    echo "Restoring: doc_087.pdf"
    mv "$SCRIPT_DIR/downloads/doc_087.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_087.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_153.pdf" ]; then
    echo "Restoring: doc_153.pdf"
    mv "$SCRIPT_DIR/downloads/doc_153.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_153.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_000.pdf" ]; then
    echo "Restoring: doc_000.pdf"
    mv "$SCRIPT_DIR/downloads/doc_000.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_000.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_103.pdf" ]; then
    echo "Restoring: doc_103.pdf"
    mv "$SCRIPT_DIR/downloads/doc_103.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_103.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_127.pdf" ]; then
    echo "Restoring: doc_127.pdf"
    mv "$SCRIPT_DIR/downloads/doc_127.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_127.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_008.pdf" ]; then
    echo "Restoring: doc_008.pdf"
    mv "$SCRIPT_DIR/downloads/doc_008.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_008.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_227.pdf" ]; then
    echo "Restoring: doc_227.pdf"
    mv "$SCRIPT_DIR/downloads/doc_227.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_227.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_211.pdf" ]; then
    echo "Restoring: doc_211.pdf"
    mv "$SCRIPT_DIR/downloads/doc_211.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_211.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_147.pdf" ]; then
    echo "Restoring: doc_147.pdf"
    mv "$SCRIPT_DIR/downloads/doc_147.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_147.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_210.pdf" ]; then
    echo "Restoring: doc_210.pdf"
    mv "$SCRIPT_DIR/downloads/doc_210.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_210.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_267.pdf" ]; then
    echo "Restoring: doc_267.pdf"
    mv "$SCRIPT_DIR/downloads/doc_267.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_267.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_093.pdf" ]; then
    echo "Restoring: doc_093.pdf"
    mv "$SCRIPT_DIR/downloads/doc_093.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_093.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_023.pdf" ]; then
    echo "Restoring: doc_023.pdf"
    mv "$SCRIPT_DIR/downloads/doc_023.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_023.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_148.pdf" ]; then
    echo "Restoring: doc_148.pdf"
    mv "$SCRIPT_DIR/downloads/doc_148.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_148.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_021.pdf" ]; then
    echo "Restoring: doc_021.pdf"
    mv "$SCRIPT_DIR/downloads/doc_021.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_021.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_171.pdf" ]; then
    echo "Restoring: doc_171.pdf"
    mv "$SCRIPT_DIR/downloads/doc_171.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_171.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_047.pdf" ]; then
    echo "Restoring: doc_047.pdf"
    mv "$SCRIPT_DIR/downloads/doc_047.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_047.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_297.pdf" ]; then
    echo "Restoring: doc_297.pdf"
    mv "$SCRIPT_DIR/downloads/doc_297.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_297.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_016.pdf" ]; then
    echo "Restoring: doc_016.pdf"
    mv "$SCRIPT_DIR/downloads/doc_016.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_016.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_231.pdf" ]; then
    echo "Restoring: doc_231.pdf"
    mv "$SCRIPT_DIR/downloads/doc_231.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_231.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_280.pdf" ]; then
    echo "Restoring: doc_280.pdf"
    mv "$SCRIPT_DIR/downloads/doc_280.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_280.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_214.pdf" ]; then
    echo "Restoring: doc_214.pdf"
    mv "$SCRIPT_DIR/downloads/doc_214.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_214.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_049.pdf" ]; then
    echo "Restoring: doc_049.pdf"
    mv "$SCRIPT_DIR/downloads/doc_049.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_049.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_085.pdf" ]; then
    echo "Restoring: doc_085.pdf"
    mv "$SCRIPT_DIR/downloads/doc_085.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_085.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_132.pdf" ]; then
    echo "Restoring: doc_132.pdf"
    mv "$SCRIPT_DIR/downloads/doc_132.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_132.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_254.pdf" ]; then
    echo "Restoring: doc_254.pdf"
    mv "$SCRIPT_DIR/downloads/doc_254.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_254.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_095.pdf" ]; then
    echo "Restoring: doc_095.pdf"
    mv "$SCRIPT_DIR/downloads/doc_095.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_095.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_173.pdf" ]; then
    echo "Restoring: doc_173.pdf"
    mv "$SCRIPT_DIR/downloads/doc_173.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_173.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_246.pdf" ]; then
    echo "Restoring: doc_246.pdf"
    mv "$SCRIPT_DIR/downloads/doc_246.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_246.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_190.pdf" ]; then
    echo "Restoring: doc_190.pdf"
    mv "$SCRIPT_DIR/downloads/doc_190.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_190.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_268.pdf" ]; then
    echo "Restoring: doc_268.pdf"
    mv "$SCRIPT_DIR/downloads/doc_268.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_268.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_286.pdf" ]; then
    echo "Restoring: doc_286.pdf"
    mv "$SCRIPT_DIR/downloads/doc_286.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_286.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_139.pdf" ]; then
    echo "Restoring: doc_139.pdf"
    mv "$SCRIPT_DIR/downloads/doc_139.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_139.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_152.pdf" ]; then
    echo "Restoring: doc_152.pdf"
    mv "$SCRIPT_DIR/downloads/doc_152.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_152.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_290.pdf" ]; then
    echo "Restoring: doc_290.pdf"
    mv "$SCRIPT_DIR/downloads/doc_290.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_290.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_228.pdf" ]; then
    echo "Restoring: doc_228.pdf"
    mv "$SCRIPT_DIR/downloads/doc_228.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_228.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_204.pdf" ]; then
    echo "Restoring: doc_204.pdf"
    mv "$SCRIPT_DIR/downloads/doc_204.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_204.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_196.pdf" ]; then
    echo "Restoring: doc_196.pdf"
    mv "$SCRIPT_DIR/downloads/doc_196.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_196.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_243.pdf" ]; then
    echo "Restoring: doc_243.pdf"
    mv "$SCRIPT_DIR/downloads/doc_243.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_243.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_038.pdf" ]; then
    echo "Restoring: doc_038.pdf"
    mv "$SCRIPT_DIR/downloads/doc_038.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_038.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_084.pdf" ]; then
    echo "Restoring: doc_084.pdf"
    mv "$SCRIPT_DIR/downloads/doc_084.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_084.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_270.pdf" ]; then
    echo "Restoring: doc_270.pdf"
    mv "$SCRIPT_DIR/downloads/doc_270.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_270.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_263.pdf" ]; then
    echo "Restoring: doc_263.pdf"
    mv "$SCRIPT_DIR/downloads/doc_263.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_263.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_014.pdf" ]; then
    echo "Restoring: doc_014.pdf"
    mv "$SCRIPT_DIR/downloads/doc_014.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_014.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_027.pdf" ]; then
    echo "Restoring: doc_027.pdf"
    mv "$SCRIPT_DIR/downloads/doc_027.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_027.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_224.pdf" ]; then
    echo "Restoring: doc_224.pdf"
    mv "$SCRIPT_DIR/downloads/doc_224.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_224.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_080.pdf" ]; then
    echo "Restoring: doc_080.pdf"
    mv "$SCRIPT_DIR/downloads/doc_080.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_080.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_118.pdf" ]; then
    echo "Restoring: doc_118.pdf"
    mv "$SCRIPT_DIR/downloads/doc_118.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_118.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_166.pdf" ]; then
    echo "Restoring: doc_166.pdf"
    mv "$SCRIPT_DIR/downloads/doc_166.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_166.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_282.pdf" ]; then
    echo "Restoring: doc_282.pdf"
    mv "$SCRIPT_DIR/downloads/doc_282.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_282.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_223.pdf" ]; then
    echo "Restoring: doc_223.pdf"
    mv "$SCRIPT_DIR/downloads/doc_223.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_223.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_182.pdf" ]; then
    echo "Restoring: doc_182.pdf"
    mv "$SCRIPT_DIR/downloads/doc_182.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_182.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_012.pdf" ]; then
    echo "Restoring: doc_012.pdf"
    mv "$SCRIPT_DIR/downloads/doc_012.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_012.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_046.pdf" ]; then
    echo "Restoring: doc_046.pdf"
    mv "$SCRIPT_DIR/downloads/doc_046.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_046.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_272.pdf" ]; then
    echo "Restoring: doc_272.pdf"
    mv "$SCRIPT_DIR/downloads/doc_272.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_272.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_253.pdf" ]; then
    echo "Restoring: doc_253.pdf"
    mv "$SCRIPT_DIR/downloads/doc_253.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_253.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_120.pdf" ]; then
    echo "Restoring: doc_120.pdf"
    mv "$SCRIPT_DIR/downloads/doc_120.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_120.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_041.pdf" ]; then
    echo "Restoring: doc_041.pdf"
    mv "$SCRIPT_DIR/downloads/doc_041.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_041.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_104.pdf" ]; then
    echo "Restoring: doc_104.pdf"
    mv "$SCRIPT_DIR/downloads/doc_104.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_104.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_262.pdf" ]; then
    echo "Restoring: doc_262.pdf"
    mv "$SCRIPT_DIR/downloads/doc_262.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_262.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_001.pdf" ]; then
    echo "Restoring: doc_001.pdf"
    mv "$SCRIPT_DIR/downloads/doc_001.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_001.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_203.pdf" ]; then
    echo "Restoring: doc_203.pdf"
    mv "$SCRIPT_DIR/downloads/doc_203.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_203.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_288.pdf" ]; then
    echo "Restoring: doc_288.pdf"
    mv "$SCRIPT_DIR/downloads/doc_288.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_288.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_287.pdf" ]; then
    echo "Restoring: doc_287.pdf"
    mv "$SCRIPT_DIR/downloads/doc_287.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_287.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_076.pdf" ]; then
    echo "Restoring: doc_076.pdf"
    mv "$SCRIPT_DIR/downloads/doc_076.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_076.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_145.pdf" ]; then
    echo "Restoring: doc_145.pdf"
    mv "$SCRIPT_DIR/downloads/doc_145.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_145.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_207.pdf" ]; then
    echo "Restoring: doc_207.pdf"
    mv "$SCRIPT_DIR/downloads/doc_207.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_207.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_256.pdf" ]; then
    echo "Restoring: doc_256.pdf"
    mv "$SCRIPT_DIR/downloads/doc_256.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_256.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_040.pdf" ]; then
    echo "Restoring: doc_040.pdf"
    mv "$SCRIPT_DIR/downloads/doc_040.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_040.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_266.pdf" ]; then
    echo "Restoring: doc_266.pdf"
    mv "$SCRIPT_DIR/downloads/doc_266.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_266.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_035.pdf" ]; then
    echo "Restoring: doc_035.pdf"
    mv "$SCRIPT_DIR/downloads/doc_035.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_035.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_294.pdf" ]; then
    echo "Restoring: doc_294.pdf"
    mv "$SCRIPT_DIR/downloads/doc_294.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_294.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_123.pdf" ]; then
    echo "Restoring: doc_123.pdf"
    mv "$SCRIPT_DIR/downloads/doc_123.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_123.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_007.pdf" ]; then
    echo "Restoring: doc_007.pdf"
    mv "$SCRIPT_DIR/downloads/doc_007.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_007.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_068.pdf" ]; then
    echo "Restoring: doc_068.pdf"
    mv "$SCRIPT_DIR/downloads/doc_068.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_068.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_100.pdf" ]; then
    echo "Restoring: doc_100.pdf"
    mv "$SCRIPT_DIR/downloads/doc_100.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_100.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_249.pdf" ]; then
    echo "Restoring: doc_249.pdf"
    mv "$SCRIPT_DIR/downloads/doc_249.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_249.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_043.pdf" ]; then
    echo "Restoring: doc_043.pdf"
    mv "$SCRIPT_DIR/downloads/doc_043.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_043.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_042.pdf" ]; then
    echo "Restoring: doc_042.pdf"
    mv "$SCRIPT_DIR/downloads/doc_042.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_042.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_187.pdf" ]; then
    echo "Restoring: doc_187.pdf"
    mv "$SCRIPT_DIR/downloads/doc_187.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_187.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_029.pdf" ]; then
    echo "Restoring: doc_029.pdf"
    mv "$SCRIPT_DIR/downloads/doc_029.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_029.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_020.pdf" ]; then
    echo "Restoring: doc_020.pdf"
    mv "$SCRIPT_DIR/downloads/doc_020.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_020.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_247.pdf" ]; then
    echo "Restoring: doc_247.pdf"
    mv "$SCRIPT_DIR/downloads/doc_247.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_247.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_226.pdf" ]; then
    echo "Restoring: doc_226.pdf"
    mv "$SCRIPT_DIR/downloads/doc_226.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_226.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_183.pdf" ]; then
    echo "Restoring: doc_183.pdf"
    mv "$SCRIPT_DIR/downloads/doc_183.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_183.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_057.pdf" ]; then
    echo "Restoring: doc_057.pdf"
    mv "$SCRIPT_DIR/downloads/doc_057.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_057.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_186.pdf" ]; then
    echo "Restoring: doc_186.pdf"
    mv "$SCRIPT_DIR/downloads/doc_186.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_186.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_131.pdf" ]; then
    echo "Restoring: doc_131.pdf"
    mv "$SCRIPT_DIR/downloads/doc_131.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_131.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_169.pdf" ]; then
    echo "Restoring: doc_169.pdf"
    mv "$SCRIPT_DIR/downloads/doc_169.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_169.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_096.pdf" ]; then
    echo "Restoring: doc_096.pdf"
    mv "$SCRIPT_DIR/downloads/doc_096.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_096.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_074.pdf" ]; then
    echo "Restoring: doc_074.pdf"
    mv "$SCRIPT_DIR/downloads/doc_074.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_074.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_289.pdf" ]; then
    echo "Restoring: doc_289.pdf"
    mv "$SCRIPT_DIR/downloads/doc_289.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_289.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_235.pdf" ]; then
    echo "Restoring: doc_235.pdf"
    mv "$SCRIPT_DIR/downloads/doc_235.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_235.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_086.pdf" ]; then
    echo "Restoring: doc_086.pdf"
    mv "$SCRIPT_DIR/downloads/doc_086.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_086.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_232.pdf" ]; then
    echo "Restoring: doc_232.pdf"
    mv "$SCRIPT_DIR/downloads/doc_232.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_232.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_124.pdf" ]; then
    echo "Restoring: doc_124.pdf"
    mv "$SCRIPT_DIR/downloads/doc_124.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_124.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_058.pdf" ]; then
    echo "Restoring: doc_058.pdf"
    mv "$SCRIPT_DIR/downloads/doc_058.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_058.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_142.pdf" ]; then
    echo "Restoring: doc_142.pdf"
    mv "$SCRIPT_DIR/downloads/doc_142.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_142.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_255.pdf" ]; then
    echo "Restoring: doc_255.pdf"
    mv "$SCRIPT_DIR/downloads/doc_255.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_255.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_107.pdf" ]; then
    echo "Restoring: doc_107.pdf"
    mv "$SCRIPT_DIR/downloads/doc_107.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_107.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_013.pdf" ]; then
    echo "Restoring: doc_013.pdf"
    mv "$SCRIPT_DIR/downloads/doc_013.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_013.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_238.pdf" ]; then
    echo "Restoring: doc_238.pdf"
    mv "$SCRIPT_DIR/downloads/doc_238.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_238.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_150.pdf" ]; then
    echo "Restoring: doc_150.pdf"
    mv "$SCRIPT_DIR/downloads/doc_150.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_150.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_197.pdf" ]; then
    echo "Restoring: doc_197.pdf"
    mv "$SCRIPT_DIR/downloads/doc_197.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_197.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_090.pdf" ]; then
    echo "Restoring: doc_090.pdf"
    mv "$SCRIPT_DIR/downloads/doc_090.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_090.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_066.pdf" ]; then
    echo "Restoring: doc_066.pdf"
    mv "$SCRIPT_DIR/downloads/doc_066.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_066.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_162.pdf" ]; then
    echo "Restoring: doc_162.pdf"
    mv "$SCRIPT_DIR/downloads/doc_162.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_162.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_161.pdf" ]; then
    echo "Restoring: doc_161.pdf"
    mv "$SCRIPT_DIR/downloads/doc_161.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_161.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_075.pdf" ]; then
    echo "Restoring: doc_075.pdf"
    mv "$SCRIPT_DIR/downloads/doc_075.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_075.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_296.pdf" ]; then
    echo "Restoring: doc_296.pdf"
    mv "$SCRIPT_DIR/downloads/doc_296.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_296.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_034.pdf" ]; then
    echo "Restoring: doc_034.pdf"
    mv "$SCRIPT_DIR/downloads/doc_034.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_034.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_229.pdf" ]; then
    echo "Restoring: doc_229.pdf"
    mv "$SCRIPT_DIR/downloads/doc_229.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_229.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_126.pdf" ]; then
    echo "Restoring: doc_126.pdf"
    mv "$SCRIPT_DIR/downloads/doc_126.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_126.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_121.pdf" ]; then
    echo "Restoring: doc_121.pdf"
    mv "$SCRIPT_DIR/downloads/doc_121.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_121.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_098.pdf" ]; then
    echo "Restoring: doc_098.pdf"
    mv "$SCRIPT_DIR/downloads/doc_098.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_098.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_188.pdf" ]; then
    echo "Restoring: doc_188.pdf"
    mv "$SCRIPT_DIR/downloads/doc_188.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_188.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_158.pdf" ]; then
    echo "Restoring: doc_158.pdf"
    mv "$SCRIPT_DIR/downloads/doc_158.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_158.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_284.pdf" ]; then
    echo "Restoring: doc_284.pdf"
    mv "$SCRIPT_DIR/downloads/doc_284.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_284.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_019.pdf" ]; then
    echo "Restoring: doc_019.pdf"
    mv "$SCRIPT_DIR/downloads/doc_019.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_019.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_025.pdf" ]; then
    echo "Restoring: doc_025.pdf"
    mv "$SCRIPT_DIR/downloads/doc_025.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_025.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_009.pdf" ]; then
    echo "Restoring: doc_009.pdf"
    mv "$SCRIPT_DIR/downloads/doc_009.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_009.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_199.pdf" ]; then
    echo "Restoring: doc_199.pdf"
    mv "$SCRIPT_DIR/downloads/doc_199.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_199.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_281.pdf" ]; then
    echo "Restoring: doc_281.pdf"
    mv "$SCRIPT_DIR/downloads/doc_281.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_281.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_062.pdf" ]; then
    echo "Restoring: doc_062.pdf"
    mv "$SCRIPT_DIR/downloads/doc_062.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_062.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_163.pdf" ]; then
    echo "Restoring: doc_163.pdf"
    mv "$SCRIPT_DIR/downloads/doc_163.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_163.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_205.pdf" ]; then
    echo "Restoring: doc_205.pdf"
    mv "$SCRIPT_DIR/downloads/doc_205.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_205.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_236.pdf" ]; then
    echo "Restoring: doc_236.pdf"
    mv "$SCRIPT_DIR/downloads/doc_236.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_236.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_065.pdf" ]; then
    echo "Restoring: doc_065.pdf"
    mv "$SCRIPT_DIR/downloads/doc_065.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_065.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_130.pdf" ]; then
    echo "Restoring: doc_130.pdf"
    mv "$SCRIPT_DIR/downloads/doc_130.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_130.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_134.pdf" ]; then
    echo "Restoring: doc_134.pdf"
    mv "$SCRIPT_DIR/downloads/doc_134.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_134.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_206.pdf" ]; then
    echo "Restoring: doc_206.pdf"
    mv "$SCRIPT_DIR/downloads/doc_206.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_206.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_184.pdf" ]; then
    echo "Restoring: doc_184.pdf"
    mv "$SCRIPT_DIR/downloads/doc_184.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_184.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_115.pdf" ]; then
    echo "Restoring: doc_115.pdf"
    mv "$SCRIPT_DIR/downloads/doc_115.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_115.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_174.pdf" ]; then
    echo "Restoring: doc_174.pdf"
    mv "$SCRIPT_DIR/downloads/doc_174.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_174.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_102.pdf" ]; then
    echo "Restoring: doc_102.pdf"
    mv "$SCRIPT_DIR/downloads/doc_102.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_102.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_071.pdf" ]; then
    echo "Restoring: doc_071.pdf"
    mv "$SCRIPT_DIR/downloads/doc_071.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_071.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_053.pdf" ]; then
    echo "Restoring: doc_053.pdf"
    mv "$SCRIPT_DIR/downloads/doc_053.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_053.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_198.pdf" ]; then
    echo "Restoring: doc_198.pdf"
    mv "$SCRIPT_DIR/downloads/doc_198.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_198.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_219.pdf" ]; then
    echo "Restoring: doc_219.pdf"
    mv "$SCRIPT_DIR/downloads/doc_219.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_219.pdf"
fi

if [ -f "$SCRIPT_DIR/downloads/doc_200.pdf" ]; then
    echo "Restoring: doc_200.pdf"
    mv "$SCRIPT_DIR/downloads/doc_200.pdf" "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_downloads_20260225_095212/documents/doc_200.pdf"
fi


echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Recovery complete!"
echo "═══════════════════════════════════════════════════════════════"
