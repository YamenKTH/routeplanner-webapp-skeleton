<template>
  <nav class="topnav">
    <div class="nav-container">
      <router-link to="/what-is-minutetour" class="nav-logo" active-class="active">
        <span class="logo-text">MinuteTour</span>
      </router-link>
      <div class="nav-links">
        <router-link to="/what-is-minutetour" active-class="active">Home</router-link>
        <router-link to="/vision" active-class="active">Pricing</router-link>
        <router-link to="/about-us" active-class="active">About</router-link>
        <router-link to="/app-demo" active-class="active" class="nav-demo">Try Demo</router-link>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.topnav {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
}
.nav-logo {
  text-decoration: none;
  color: #111;
  font-weight: 700;
  font-size: 1.25rem;
  letter-spacing: -0.02em;
  transition: transform 0.2s ease;
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

@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
  .nav-links {
    gap: 1rem;
    flex-wrap: wrap;
    justify-content: center;
  }
  .nav-links a {
    font-size: 0.9rem;
  }
}
</style>
