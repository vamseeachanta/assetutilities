$(document).ready(function() {
    
    $('#theMenu').accordion({
        
        active: false,
        collapsible: true,
        heightStyle: "content"
        
    });
    
});

 $(document).scroll(function(){
         
        var scrollPos = $(this).scrollTop();
         
        if(scrollPos > 60) {
             
            $('#theMenu').fadeIn();
             
        } else { 
             
            $('#theMenu').hide();
             
        }
         
    });

function scrollToDiv(div) {
    
    $('html, body').animate({
		scrollTop: $(div).offset().top
	},1000);
    
}
    
    