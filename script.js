document.addEventListener('DOMContentLoaded', function() {
    // Menu toggle para móviles
    const menuToggle = document.querySelector('.menu-toggle');
    const mainNav = document.querySelector('.main-nav');
    
    menuToggle.addEventListener('click', function() {
      mainNav.classList.toggle('active');
      this.innerHTML = mainNav.classList.contains('active') ? 
        '<i class="bi bi-x"></i>' : '<i class="bi bi-list"></i>';
    });
    
    // Cerrar menú al hacer clic en un enlace
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', function() {
        if (mainNav.classList.contains('active')) {
          mainNav.classList.remove('active');
          menuToggle.innerHTML = '<i class="bi bi-list"></i>';
        }
      });
    });


        
        // Marcar el enlace activo según la URL actual
        const currentPage = location.pathname.split('/').pop() || 'index.html';
        
        navLinks.forEach(link => {
          const linkPage = link.getAttribute('href').split('/').pop();
        
          if (linkPage === currentPage) {
            link.classList.add('active');
          } else {
            link.classList.remove('active');
          }
        });
    
    // Acordeón de preguntas frecuentes
    const accordionBtns = document.querySelectorAll('.accordion-btn');
    accordionBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        this.classList.toggle('active');
        const content = this.nextElementSibling;
        
        if (this.classList.contains('active')) {
          content.style.maxHeight = content.scrollHeight + 'px';
        } else {
          content.style.maxHeight = '0';
        }
      });
    });
    
    // Tabs de productos
    const tabBtns = document.querySelectorAll('.tab-btn');
    const productsGrid = document.querySelector('.products-grid');
    
    // Datos de productos (simulados)
    const productsData = {
      switches: [
        { name: 'Switch Cisco 2960', desc: '24 puertos Gigabit Ethernet', price: '$1,200' },
        { name: 'Switch HP 1820', desc: '8 puertos Gigabit', price: '$350' },
        { name: 'Switch Ubiquiti USW', desc: '16 puertos PoE', price: '$899' }
      ],
      routers: [
        { name: 'Router Cisco ISR', desc: 'Para empresas medianas', price: '$2,500' },
        { name: 'Router MikroTik', desc: 'Potente y económico', price: '$199' }
      ],
      wifi: [
        { name: 'AP Ubiquiti UAP', desc: 'Wi-Fi 6, alta densidad', price: '$179' },
        { name: 'AP Cisco 2802', desc: 'Empresarial, doble banda', price: '$699' }
      ],
      cableado: [
        { name: 'Cable UTP Cat6', desc: 'Caja 305m', price: '$150' },
        { name: 'Fibra óptica', desc: 'Multimodo 50/125', price: '$0.80/m' }
      ],
      herramientas: [
        { name: 'Probador de red', desc: 'Fluke básico', price: '$299' },
        { name: 'Crimpadora RJ45', desc: 'Profesional', price: '$49' }
      ]
    };
    
    // Función para cargar productos
    function loadProducts(category) {
      productsGrid.innerHTML = '';
      const products = productsData[category];
      
      products.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'product-card';
        productCard.innerHTML = `
          <div class="product-image">
            <i class="bi bi-hdd-network"></i>
          </div>
          <div class="product-info">
            <h3>${product.name}</h3>
            <p>${product.desc}</p>
            <span class="product-price">${product.price}</span>
            <a href="#contacto" class="product-btn">Cotizar</a>
          </div>
        `;
        productsGrid.appendChild(productCard);
      });
    }
    
    // Eventos para los tabs
    tabBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        // Remover clase active de todos los botones
        tabBtns.forEach(b => b.classList.remove('active'));
        // Agregar clase active al botón clickeado
        this.classList.add('active');
        // Cargar productos correspondientes
        loadProducts(this.dataset.category);
      });
    });
    
    // Cargar productos iniciales
    loadProducts('switches');
    


    

    







    
    // Observador de intersección para las secciones
    const observerOptions = {
      threshold: 0.1
    };
    
    const observer = new IntersectionObserver(function(entries) {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          const correspondingLink = document.querySelector(`.nav-link[href="#${id}"]`);
          
          navLinks.forEach(link => link.classList.remove('active'));
          if (correspondingLink) {
            correspondingLink.classList.add('active');
          }
          
          const header = document.querySelector('.main-header');
          header.className = `main-header ${id} scrolled`;
        }
      });
    }, observerOptions);
    
    sections.forEach(section => {
      observer.observe(section);
    });
    
    
    // Formulario de contacto
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
      contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        alert('Gracias por tu mensaje. Nos pondremos en contacto contigo pronto.');
        this.reset();
      });
    }
  });







  const images = [
    '/IMAGENES/desktop-wallpaper-telecomunications-radar.jpg',
    '/IMAGENES/datacenter.jpg',
    '/IMAGENES/photo-1446776653964-20c1d3a81b06.avif',
    '/IMAGENES/photo-1528499908559-b8e4e8b89bda.avif',
    '/IMAGENES/pngtree-telecom-tower-close(3).jpg'

    ];
  
  let index = 1;
  let showingBg1 = true;
  
  const bg1 = document.querySelector('.hero-bg1');
  const bg2 = document.querySelector('.hero-bg2');
  
  function cambiarFondo() {
    const nextImage = `linear-gradient(rgba(140, 154, 216, 0.03), rgba(10, 0, 104, 0.22)), url('${images[index]}')`;
    
    if (showingBg1) {
      bg2.style.backgroundImage = nextImage;
      bg2.style.opacity = 1;
      bg1.style.opacity = 0;
    } else {
      bg1.style.backgroundImage = nextImage;
      bg1.style.opacity = 1;
      bg2.style.opacity = 0;
    }
  
    showingBg1 = !showingBg1;
    index = (index + 1) % images.length;
  }
  
  setInterval(cambiarFondo, 3000);
  
  
  