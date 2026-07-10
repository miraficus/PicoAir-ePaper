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
        chamferCube([78, 38, 19], [[0, 0, 1, 1], [0, 1, 1, 0], [1, 1, 1, 1]], 0.5);
    
        color("grey")
        translate([58,5,18])
        cube([17,30,3]); 
        
        color("grey")
        translate([7,8,18])
        cube([17,15,3]); 
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

module caseholdsholes() {
    difference() {
        cutcase();
        
        translate([0,0,16])
        color("blue")
        caseholds();
    }     
}

module pico() {
    translate([1,9.5,15])
    cube([51.2,21,1]);

    translate([-1,16,15.5])
    color("red")
    chamferCube([8, 8, 3], [[1, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], 1.5);

    translate([1,15,16])
    color("pink")
    cube([6,10,3]);
    
    color("green")
    translate([46.2,17.5,16])
    cube([6,5,2]);

    color("white")
    translate([1,9.5,16])
    cube([5,2,3]);

    color("white")
    translate([1,28.5,16])
    cube([5,2,3]);
    
}

module picoholder() {
    color("lightblue")
    translate([46.2,8.5,15])
    cube([8,23,4]);

    color("lightblue")
    translate([0,8.5,15])
    cube([5,23,4]);
}

difference() {
    picoholder();
    pico();
}

difference() {
    caseholdsholes();
    pico();
}



//picoholder();
//pico();        
magnetholds();
caseholds();    
//caseholdsholes();     
    
    