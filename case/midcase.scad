echo(version=version());

//Chamfer Library
/* https://github.com/SebiTimeWaster/Chamfers-for-OpenSCAD */
include <Chamfers-for-OpenSCAD/Chamfer.scad>;

    
/* [Customizer] */
// Increase the visual detail
$fn = 100;


module case() {
    color("white")
    chamferCube([80, 40, 20], [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1]], 0.5);
}

module cutcase() {
    difference() {
    case();
    
    translate([1,1,0])
    chamferCube([78, 38, 18], [[0, 0, 1, 1], [0, 1, 1, 0], [1, 1, 1, 1]], 0.5);
    }
}  
 
module magnethold() {
    difference() {
        translate([3,3,0])
        color("red")
        cylinder(d=6, h=18);
        
        translate([3,3,0])
        color("pink")
        cylinder(d=4, h=7); 
    }
}

module magnetholds() {
    magnethold();

    translate([74,0,0])
    magnethold();

    translate([0,34,0])
    magnethold();
    
    translate([74,34,0])
    magnethold();    
}

module caseholds() {
    translate([1,15,-2])
    color("lightgreen")
    chamferCube([1, 12, 8], [[1, 1, 0, 0], [1, 0, 1, 1], [0, 0, 0, 0]], 0.5);

    translate([78,15,-2])
    color("lightgreen")
    chamferCube([1, 12, 8], [[1, 1, 0, 0], [1, 1, 0, 1], [0, 0, 0, 0]], 0.5);

    rotate([0,0,90])
    translate([1,-70,-2])
    color("lightgreen")
    chamferCube([1, 12, 8], [[1, 1, 0, 0], [1, 0, 1, 1], [0, 0, 0, 0]], 0.5);
 
    rotate([0,0,90])
    translate([1,-22,-2])
    color("lightgreen")
    chamferCube([1, 12, 8], [[1, 1, 0, 0], [1, 0, 1, 1], [0, 0, 0, 0]], 0.5);
  
    rotate([0,0,270])
    translate([-39,10,-2])
    color("lightgreen")
    chamferCube([1, 12, 8], [[1, 1, 0, 0], [1, 0, 1, 1], [0, 0, 0, 0]], 0.5);
   
    rotate([0,0,270])
    translate([-39,58,-2])
    color("lightgreen")
    chamferCube([1, 12, 8], [[1, 1, 0, 0], [1, 0, 1, 1], [0, 0, 0, 0]], 0.5);

 
 
}




cutcase();        
magnetholds();
caseholds();    
    
    
    