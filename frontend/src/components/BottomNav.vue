<template>
  <nav class="bottom-nav">
    <router-link to="/app-demo/map" class="nav-btn" active-class="active">
      🗺️ <span>Map</span>
    </router-link>
    <router-link to="/app-demo/explore" class="nav-btn" active-class="active">
      🔎 <span>Explore</span>
    </router-link>
    <router-link to="/app-demo/profile" class="nav-btn" active-class="active">
      👤 <span>Profile</span>
    </router-link>
  </nav>
</template>

<style scoped>
.bottom-nav {
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: #ffffff;
  border-top: 1px solid #ddd;
  padding: 0.6rem 0.3rem;
  box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.05);
  z-index: 1000;
}

/* Each button */
.nav-btn {
  flex: 1;
  text-align: center;
  padding: 0.6rem 0.3rem;
  font-size: 1.2rem;
  color: #555;
  border-radius: 10px;
  transition: all 0.25s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

/* Text under icon */
.nav-btn span {
  font-size: 0.8rem;
  margin-top: 2px;
}

/* Hover effect */
.nav-btn:hover {
  background: rgba(0, 123, 255, 0.1);
  color: #007bff;
  transform: translateY(-2px);
}

/* Active (clicked / current route) */
.active {
  background: #007bff;
  color: white;
  box-shadow: 0 3px 8px rgba(0, 123, 255, 0.3);
}

/* Active text color */
.active span {
  color: white;
}
</style>
