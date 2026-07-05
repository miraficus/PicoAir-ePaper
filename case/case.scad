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
chamferCube([4, 8, 1], [[1, 1, 0, 0], [0, 0, 0, 1], [0, 1, 1, 0]], 0.5);

translate([69,28,7])
color("lightgreen")
chamferCube([4, 8, 1], [[1, 1, 0, 0], [0, 0, 0, 1], [0, 1, 1, 0]], 0.5);

translate([1.5,14,7])
color("lightgreen")
chamferCube([4, 12, 1], [[1, 1, 0, 0], [0, 0, 0, 1], [0, 1, 1, 0]], 0.5);
}
    
frontcase();    
displayholds();    

    
    
    
    