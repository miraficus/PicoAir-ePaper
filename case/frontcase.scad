echo(version=version());

//Chamfer Library
/* https://github.com/SebiTimeWaster/Chamfers-for-OpenSCAD */
include <Chamfers-for-OpenSCAD/Chamfer.scad>;

    
/* [Customizer] */
// Increase the visual detail
$fn = 100;

module display() {
    color("red")
    translate([0,-0.25,0])
    chamferCube([65.5, 30.5, 2], [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1]], 1);
    
    color("pink")
    translate([2,0,2])
    cube([62,30,1]);
    
    color("blue")
    translate([5,2,3])
    chamferCube([51, 26, 1], [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1]], 0.5);
    
    color("lightblue")
    translate([62,7,0])
    cube([8,16,3]);
}

module casefront() {
    color("white")
    chamferCube([80, 40, 12], [[0, 0, 1, 1], [0, 1, 1, 0], [1, 1, 1, 1]], 0.5);
    
}

module frontcase() {
    difference() {
    casefront();

    translate([5,5,8])
    display();
    
    translate([1,1,0])
    chamferCube([78, 38, 8], [[0, 0, 1, 1], [0, 1, 1, 0], [1, 1, 1, 1]], 0.5);

    }
}  

module displayholds() {
    translate([69,4,7])
    color("lightgreen")
    chamferCube([4, 8, 1], [[1, 0, 0, 0], [0, 0, 0, 1], [0, 1, 0, 0]], 0.5);

    translate([69,28,7])
    color("lightgreen")
    chamferCube([4, 8, 1], [[0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], 0.5);

    translate([1.5,14,7])
    color("lightgreen")
    chamferCube([4, 12, 1], [[1, 1, 0, 0], [0, 0, 0, 1], [0, 1, 1, 0]], 0.5);
}
 
module magnethold() {
    difference() {
        translate([3,3,0])
        color("red")
        cylinder(d=6, h=11);
        
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





 
frontcase();    
displayholds();    
magnetholds();
    
    
    
    