$(document).ready(function(){

    loadGallery(true, 'a.thumbnail');

    //This function disables buttons when needed
    function disableButtons(counter_max, counter_current){
        $('#show-previous-image, #show-next-image').show();
        if(counter_max == counter_current){
            $('#show-next-image').hide();
        } else if (counter_current == 1){
            $('#show-previous-image').hide();
        }
    }

    /**
     *
     * @param setIDs        Sets IDs when DOM is loaded. If using a PHP counter, set to false.
     * @param setClickAttr  Sets the attribute for the click handler.
     */

    function loadGallery(setIDs, setClickAttr){
        var current_image,
            selector,
            counter = 0;

        $('#show-next-image, #show-previous-image').click(function(){
            if($(this).attr('id') == 'show-previous-image'){
                current_image--;
            } else {
                current_image++;
            }

            selector = $('[data-image-id="' + current_image + '"]');
            updateGallery(selector);
        });

        function updateGallery(selector) {
            var $sel = selector;
            current_image = $sel.data('image-id');
            $('#image-gallery-caption').text($sel.data('caption'));
            $('#image-gallery-title').text($sel.data('title'));
            $('#image-gallery-image').attr('src', $sel.data('image'));
            disableButtons(counter, $sel.data('image-id'));
        }
		
		function updateGallery(selector) {
            var $sel = selector;
            current_image = $sel.data('image-id2');
            $('#image-gallery-caption2').text($sel.data('caption2'));
            $('#image-gallery-title2').text($sel.data('title2'));
            $('#image-gallery-image2').attr('src', $sel.data('image2'));
            disableButtons(counter, $sel.data('image-id2'));
        }
		
		/* vessel data */
		
		function updateGallery(selector) {
            var $sel = selector;
            current_image = $sel.data('image-id3');
            $('#image-gallery-caption3').text($sel.data('caption3'));
            $('#image-gallery-title3').text($sel.data('title3'));
            $('#image-gallery-image3').attr('src', $sel.data('image3'));
            disableButtons(counter, $sel.data('image-id3'));
        }
		
		/* force coefficients */
		
		function updateGallery(selector) {
            var $sel = selector;
            current_image = $sel.data('image-id4');
            $('#image-gallery-caption4').text($sel.data('caption4'));
            $('#image-gallery-title4').text($sel.data('title4'));
            $('#image-gallery-image4').attr('src', $sel.data('image4'));
            disableButtons(counter, $sel.data('image-id4'));
        }
		
		function updateGallery(selector) {
            var $sel = selector;
            current_image = $sel.data('image-id5');
            $('#image-gallery-caption5').text($sel.data('caption5'));
            $('#image-gallery-title5').text($sel.data('title5'));
            $('#image-gallery-image5').attr('src', $sel.data('image5'));
            disableButtons(counter, $sel.data('image-id5'));
        }
		
		function updateGallery(selector) {
            var $sel = selector;
            current_image = $sel.data('image-id6');
            $('#image-gallery-caption6').text($sel.data('caption6'));
            $('#image-gallery-title6').text($sel.data('title6'));
            $('#image-gallery-image6').attr('src', $sel.data('image6'));
            disableButtons(counter, $sel.data('image-id6'));
        }
		
		function updateGallery(selector) {
            var $sel = selector;
            current_image = $sel.data('image-id7');
            $('#image-gallery-caption7').text($sel.data('caption7'));
            $('#image-gallery-title7').text($sel.data('title7'));
            $('#image-gallery-image7').attr('src', $sel.data('image7'));
            disableButtons(counter, $sel.data('image-id7'));
        }
		
		function updateGallery(selector) {
            var $sel = selector;
            current_image = $sel.data('image-id9');
            $('#image-gallery-caption9').text($sel.data('caption9'));
            $('#image-gallery-title9').text($sel.data('title9'));
            $('#image-gallery-image9').attr('src', $sel.data('image9'));
            disableButtons(counter, $sel.data('image-id9'));
        }
		
				function updateGallery(selector) {
            var $sel = selector;
            current_image = $sel.data('image-id10');
            $('#image-gallery-caption10').text($sel.data('caption10'));
            $('#image-gallery-title10').text($sel.data('title10'));
            $('#image-gallery-image10').attr('src', $sel.data('image10'));
            disableButtons(counter, $sel.data('image-id10'));
        }

        if(setIDs == true){
            $('[data-image-id]').each(function(){
                counter++;
                $(this).attr('data-image-id',counter);
            });
        }
        $(setClickAttr).on('click',function(){
            updateGallery($(this));
        });
		
    }
});