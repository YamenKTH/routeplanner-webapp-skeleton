<template>
  <nav class="bottom-nav" role="navigation" aria-label="Primary">
    <router-link to="/app-demo/map" class="nav-btn" active-class="active" aria-label="Map">
      <img :src="mapIcon" alt="Map" class="nav-icon" />
    </router-link>

    <router-link to="/app-demo/explore" class="nav-btn" active-class="active" aria-label="Explore">
      <img :src="exploreIcon" alt="Explore" class="nav-icon" />
    </router-link>

    <router-link to="/app-demo/profile" class="nav-btn" active-class="active" aria-label="Profile">
      <img :src="profileIcon" alt="Profile" class="nav-icon" />
    </router-link>
  </nav>
</template>

<script setup>
const mapIcon = new URL('/src/icons/mapIcon.png', import.meta.url).href
const exploreIcon = new URL('/src/icons/exploreIcon.png', import.meta.url).href
const profileIcon = new URL('/src/icons/profileIcon.png', import.meta.url).href
</script>



<style scoped>
:root{
  /* Set this to your phone viewport width */
  --app-max-w: 420px;    /* 360–430px typical */
  --bottom-nav-h: 52px;  /* keep in sync with MapView padding-bottom */
}

.nav-icon {
  width: 33px;
  height: 33px;
  object-fit: contain;
  transition: filter 0.2s ease;
  
}

.active .nav-icon {
  filter: brightness(1.2);
}


.active{
  background: linear-gradient(135deg, #6a5cff 0%, #ff3db3 100%);
  color: #fff;
  box-shadow: 0 6px 18px rgba(216, 131, 131, 0.35);
}
</style>

<style scoped>
:root{
  /* Set this to your phone viewport width */
  --app-max-w: 420px;    /* 360–430px typical */
  --bottom-nav-h: 52px;  /* keep in sync with MapView padding-bottom */
}

/* Centered, constrained, below everything (z < sheet) */
.bottom-nav{
  position: sticky;
  bottom: 1%;
  width: 100%;
  height: 6%;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  z-index:1000 /* your bottom sheet is ~1002, so this sits under it */
}

.nav-btn:not(:last-child) {
  border-right: 2px solid rgb(0, 0, 0);
}

.nav-btn{
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.4rem;
  color: rgb(255, 255, 255);
  transition: all 0.2s ease-in-out;
  background-color: #ffffff;
}
.nav-btn:hover{
  transform: translateY(-1px);
  background: rgba(86, 92, 95, 0.911);
}

</style>

