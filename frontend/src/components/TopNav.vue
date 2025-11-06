<template>
  <nav class="topnav">
    <div class="nav-container">
      <router-link to="/what-is-x" class="nav-logo" active-class="active">
        <span class="logo-text">MinuteTour</span>
      </router-link>
      
      <!-- Burger Menu Button (Mobile Only) -->
      <button class="burger-menu" @click="toggleMenu" aria-label="Toggle navigation menu">
        <span class="burger-line"></span>
        <span class="burger-line"></span>
        <span class="burger-line"></span>
      </button>
      
      <div class="nav-links" :class="{ 'mobile-visible': isMenuOpen }">
        <router-link to="/what-is-x" active-class="active" @click="closeMenu">Home</router-link>
        <router-link to="/vision" active-class="active" @click="closeMenu">Pricing</router-link>
        <router-link to="/about-us" active-class="active" @click="closeMenu">About</router-link>
        <router-link to="/app-demo" active-class="active" class="nav-demo" @click="closeMenu">Try Demo</router-link>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const isMenuOpen = ref(false);

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value;
  document.body.style.overflow = isMenuOpen.value ? 'hidden' : '';
};

const closeMenu = () => {
  isMenuOpen.value = false;
  document.body.style.overflow = '';
};

const handleResize = () => {
  if (window.innerWidth > 768) {
    closeMenu();
  }
};

onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  document.body.style.overflow = '';
});
</script>

<style scoped>
.topnav {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 2000; /* Increased to be above map elements */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  position: relative;
}

.nav-logo {
  text-decoration: none;
  color: #111;
  font-weight: 700;
  font-size: 1.25rem;
  letter-spacing: -0.02em;
  transition: transform 0.2s ease;
  z-index: 1001;
}

.nav-logo:hover {
  transform: scale(1.05);
}

.logo-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Burger Menu Styles */
.burger-menu {
  display: none;
  flex-direction: column;
  justify-content: space-between;
  width: 30px;
  height: 21px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  z-index: 1001;
}

.burger-line {
  display: block;
  height: 3px;
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
  transition: all 0.3s ease;
}

.nav-links {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.nav-links a {
  color: #555;
  text-decoration: none;
  font-size: 0.95rem;
  font-weight: 500;
  position: relative;
  transition: color 0.2s ease;
  padding: 0.5rem 0;
}

.nav-links a:hover {
  color: #111;
}

.nav-links a::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
}

.nav-links a:hover::after,
.nav-links a.active::after {
  width: 100%;
}

.nav-links a.active {
  color: #111;
}

.nav-demo {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white !important;
  padding: 0.5rem 1.25rem !important;
  border-radius: 8px;
  margin-left: 0.5rem;
}

.nav-demo::after {
  display: none;
}

.nav-demo:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* Mobile Styles */
@media (max-width: 768px) {
  .burger-menu {
    display: flex;
    z-index: 2002; /* Increased to be above all other elements */
  }

  .nav-links {
    position: fixed;
    top: 0;
    right: -100%;
    width: 75%;
    max-width: 300px;
    height: 100vh;
    background: white;
    flex-direction: column;
    justify-content: flex-start;
    padding: 6rem 2rem 2rem;
    gap: 1.5rem;
    box-shadow: -5px 0 15px rgba(0, 0, 0, 0.1);
    transition: right 0.3s ease-in-out;
    z-index: 2001; /* Increased to be above all other elements except burger icon */
  }

  .nav-links.mobile-visible {
    right: 0;
  }

  .nav-links a {
    width: 100%;
    padding: 0.75rem 0;
    font-size: 1.1rem;
    border-bottom: 1px solid #eee;
  }

  .nav-demo {
    margin: 1rem 0 0;
    text-align: center;
    width: 100%;
  }

  /* Overlay when menu is open */
  .nav-links.mobile-visible::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 2000; /* Increased to be above map but below menu */
  }
}
</style>
