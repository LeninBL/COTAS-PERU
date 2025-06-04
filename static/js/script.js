document.addEventListener("DOMContentLoaded", function () {
  // Menu toggle para móviles
  const menuToggle = document.querySelector(".menu-toggle");
  const mainNav = document.querySelector(".main-nav");

  menuToggle.addEventListener("click", function () {
    mainNav.classList.toggle("active");
    this.innerHTML = mainNav.classList.contains("active")
      ? '<i class="bi bi-x"></i>'
      : '<i class="bi bi-list"></i>';
  });

  // Cerrar menú al hacer clic en un enlace
  const navLinks = document.querySelectorAll(".nav-link");
  navLinks.forEach((link) => {
    link.addEventListener("click", function () {
      if (mainNav.classList.contains("active")) {
        mainNav.classList.remove("active");
        menuToggle.innerHTML = '<i class="bi bi-list"></i>';
      }
    });
  });

  // Marcar el enlace activo según la URL actual
  const currentPage = location.pathname.split("/").pop() || "index.html";

  navLinks.forEach((link) => {
    const linkPage = link.getAttribute("href").split("/").pop();

    if (linkPage === currentPage) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });

  // Acordeón de preguntas frecuentes
  const accordionBtns = document.querySelectorAll(".accordion-btn");
  accordionBtns.forEach((btn) => {
    btn.addEventListener("click", function () {
      this.classList.toggle("active");
      const content = this.nextElementSibling;

      if (this.classList.contains("active")) {
        content.style.maxHeight = content.scrollHeight + "px";
      } else {
        content.style.maxHeight = "0";
      }
    });
  });

  // Formulario de contacto
  const contactForm = document.getElementById("contactForm");
  if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
      e.preventDefault();
      alert(
        "Gracias por tu mensaje. Nos pondremos en contacto contigo pronto."
      );
      this.reset();
    });
  }
});

const images = [
  "/static/assets/IMAGENES/datacenter.webp",
  "/static/assets/IMAGENES/photo-1446776653964-20c1d3a81b06.avif",
  "/static/assets/IMAGENES/pngtree-telecom-tower-close(3).webp",
  "/static/assets/IMAGENES/photo-1528499908559-b8e4e8b89bda.avif",
  "/static/assets/IMAGENES/desktop-wallpaper-telecomunications-radar.webp",
];

let index = 1;
let showingBg1 = true;

const bg1 = document.querySelector(".hero-bg1");
const bg2 = document.querySelector(".hero-bg2");

function cambiarFondo() {
  const nextImage = `url('${images[index]}')`;

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
const heroSection = document.querySelector(".hero");

const accordion1Items = document.querySelectorAll(".accordion1-item");

accordion1Items.forEach((item) => {
  const button = item.querySelector(".accordion1-button");

  button.addEventListener("click", () => {
    const isActive = item.classList.contains("active");

    // Cerrar todos los acordeones primero
    accordion1Items.forEach((i) => {
      i.classList.remove("active");
      i.querySelector(".accordion1-content").style.maxHeight = null;
    });

    // Abrir el acordeón clickeado si no estaba activo
    if (!isActive) {
      item.classList.add("active");
      const content = item.querySelector(".accordion1-content");
      content.style.maxHeight = content.scrollHeight + "px";
    }
  });
});

const observer1 = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = 1;
        entry.target.style.transform = "translateY(0)";
      }
    });
  },
  { threshold: 0.1 }
);

document.querySelectorAll(".animate-card").forEach((card) => {
  observer1.observe(card);
});

const heroObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting) {
    setInterval(cambiarFondo, 1500);
    heroObserver.disconnect();
  }
});

heroObserver.observe(heroSection);
