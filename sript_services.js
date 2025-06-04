document.addEventListener('DOMContentLoaded', function() {
    const aosElements = document.querySelectorAll('[data-aos]');
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('aos-animate');
        }
      });
    }, {
      threshold: 0.1
    });
    
    aosElements.forEach(element => {
      observer.observe(element);
    });
  });