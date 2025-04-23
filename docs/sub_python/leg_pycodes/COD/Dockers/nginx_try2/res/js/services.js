/* 
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
function getContent(opt){
    
    var obj =document.getElementById('content');
    switch(opt){
        case 1 :
            obj.innerHTML = "<img src='res/images/gallary/services/hairCut.png'> ";
            break;
        case 2 :
            obj.innerHTML = "<img src='res/images/gallary/services/razor.png'><br><p>Razor Cutting is a hair cutting process in which sharp, knife like razors are used to excise, slice and texturize hair</p> ";
            break;
        case 3 :
            obj.innerHTML = "<img src='res/images/gallary/services/shampoo.png'><br><p> A shampoo that gives nourishment and extra conditioning to each strand of hair to make it healthy and silk-soft </p>";
            break;
        case 4 :
            obj.innerHTML = "<img src='res/images/gallary/services/foil.png'><br><p>Foil techniques give you more control over the placement of color, while still offering depth and contrast to your hair.</p>";
            break;
        case 5 :
            obj.innerHTML = "<img src='res/images/gallary/services/color.png'><br><p>Hair coloring is the practice of changing the color of hair.</p> ";
            break;
        case 6 :
            obj.innerHTML = "<img src='res/images/gallary/services/colorCorrective.png'><br><p> Corrective color is a color process that must be performed by a professional stylist to correct any and all damage caused by a color service gone bad. </p> ";
            break;
        case 7 :
            obj.innerHTML = "<img src='res/images/gallary/services/perms.png'><br><p>A permanent wave, commonly called a perm, involves the use of chemicals to break and reform the bonds of the hair. The hair is washed and wrapped on a perm rod and waving lotion is applied with a base </p>";
            break;
        case 8 :
            obj.innerHTML = "<img src='res/images/gallary/services/updo.png'><br><p>Updos for hair look great and give a smart appearance</p> ";
            break;
        case 9 :
            obj.innerHTML = "<img src='res/images/gallary/services/keratin.png'><br><p>Keratin Shot Straightening Cream is a revolutionary treatment to aid the straightening process. It works by adding keratin and modifying the shape of the hair. This system has several benefits including the amazing recovery of natural moisture, shine and silkiness, extra volume control and longer lasting straight hair. </p> ";
            break;
        case 10 :
            obj.innerHTML = "<h2>Deep Treatments</h2><br><p>Deep Treatment Hair Mask is an at-home deep treatment that brings out the natural beauty of hair</p>"+
                "<p>This exclusive formulation works deeply into the hair core, reinvigorating and repairing strand by strand, without weighing down or leaving your hair greasy."+

                "Deep Treatment Hair Mask intensely nourishes you hair, leaving it improved texture, more body, and easy to manage and with luminous shine.</p> ";
            break;
        case 11 :
            obj.innerHTML =  "<img src='res/images/gallary/services/facial.png'><br><p>Facial hair waxing is fairly quick, gets even the fine hairs, and can last weeks at a time if performed the right way</p> ";
                break;
        
        
    }

    $(obj).hide().fadeIn(2000, null);
}

