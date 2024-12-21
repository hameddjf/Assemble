document.addEventListener('DOMContentLoaded', function() {
    var showPass = document.querySelectorAll('.btn-show-pass');
    
    showPass.forEach(function(button) {
        var isShowing = false;
        
        button.addEventListener('click', function() {
            var input = this.parentElement.querySelector('input');
            var icon = this.querySelector('i');
            
            isShowing = !isShowing;
            
            if (isShowing) {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
});