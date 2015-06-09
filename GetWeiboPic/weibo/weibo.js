window.onload=function(){
    var img = document.querySelectorAll(".pic img");
    var len = img.length;
    var padding = 80
    for (var i = 0; i < len; i++){
        img[i].onclick = function(){
            if (this.offsetWidth <= 100 || this.offsetHeight <= 100){
                var width = window.innerWidth - padding > this.naturalWidth ? this.naturalWidth : window.innerWidth - padding;
                var height = this.naturalHeight * (width / this.naturalWidth)
                //alert('real : ' + this.naturalWidth + ',' + this.naturalHeight + '\nwindow : ' + window.innerWidth + ',' + window.innerHeight + '\nnow : ' + width + ',' + height)
                this.style.maxWidth = width;
                this.style.maxHeight = height;
                this.style.cursor = "zoom-out";
            }else{
                // alert(this.width)
                this.style.maxWidth = 100;
                this.style.maxHeight = 100;
                this.style.cursor = "zoom-in";
            }
        }
    }
}