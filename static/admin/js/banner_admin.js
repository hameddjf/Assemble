// admin/js/banner_admin.js

function toggleMediaInput(value) {
    const imageField = document.querySelector('#id_image');  // فیلد تصویر
    const videoField = document.querySelector('#id_video_url');  // فیلد ویدیو
    const isImageSelected = value === 'image';
    
    // مخفی یا نمایان کردن فیلدها بر اساس نوع انتخابی
    if (isImageSelected) {
        imageField.parentElement.style.display = 'block';  // نمایش فیلد تصویر
        videoField.parentElement.style.display = 'none';   // مخفی کردن فیلد ویدیو
    } else {
        imageField.parentElement.style.display = 'none';   // مخفی کردن فیلد تصویر
        videoField.parentElement.style.display = 'block';  // نمایش فیلد ویدیو
    }
}

// اجرای تابع در بارگذاری
document.addEventListener('DOMContentLoaded', function () {
    const bannerTypeSelector = document.querySelector('#id_banner_type');
    toggleMediaInput(bannerTypeSelector.value);  // مخفی کردن فیلدها بر اساس انتخاب آغازین
});
