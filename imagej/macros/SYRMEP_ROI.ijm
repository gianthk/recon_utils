width = getWidth;
height = getHeight;
depth = nSlices;
getPixelSize(unit, pw, ph, pd);

// clears the log
print("\\Clear");

setTool("point");
    waitForUser("Select center points for all areas of interest. Click OK when done")
    run("Clear Results");
    run("Measure");
    for (i=0; i<nResults; i++) {
   	px = getResult("X",i);
	py = getResult("Y",i);
	// makePoint(px, py, "large yellow hybrid add");
    run("Select None");
    run("Close");	// closes measurement panel
    print("Move X-micrometer to: " + (height/2-py)*ph+" " + unit);
	print("Move Y-micrometer to: " + -(width/2-px)*pw+" " + unit);
    }
setTool("rectangle");

if (isOpen("ROI Manager")) {
	selectWindow("ROI Manager");
	run("Close");
	}

// print("Size: " + width*pw+"x"+height*ph+"x"+depth*pd+" " + unit);
// print("Center: " + width/2+" X; "+height/2+" Y [pixels]");

//if (unit!="pixel" || pd!=1) {
//	print("Pixel Size: "+pw+"x"+ph+"x"+pd + " " + unit);
//	}
