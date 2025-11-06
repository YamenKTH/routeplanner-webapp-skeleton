<template>
  <div class="landing">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="brand">MinuteTour</h1>
        <p class="tagline">Personalized city tours in minutes — tailored to your time, interests, and location.</p>
        <div class="cta-group">
          <router-link to="/app-demo" class="btn btn-primary">Try Demo</router-link>
          <a class="btn btn-secondary" href="#learn-more">Learn More</a>
        </div>
        <div class="hero-badges">
          <div class="badge"><img class="icon" src="../icons/mapIcon.png" alt="Map" /><span>Time‑aware routes</span></div>
          <div class="badge"><img class="icon" src="../icons/exploreIcon.png" alt="Explore" /><span>Instant discovery</span></div>
          <div class="badge"><img class="icon" src="../icons/roundTripIcon.jpg" alt="Route" /><span>Flexible starts</span></div>
        </div>
      </div>
      <div class="hero-visual" aria-hidden="true">
        <div class="device-mockup">
          <img class="mock-map" src="../images/map.svg" alt="Stylized city map" />
        </div>
      </div>
    </section>

    <!-- Benefits Sections -->
    <section id="learn-more" class="benefits-intro">
      <h2>Why MinuteTour</h2>
    </section>

    <!-- Effortless Planning -->
    <section class="benefit-section">
      <div class="benefit-content">
        <div class="benefit-text">
          <h3>Effortless Planning</h3>
          <p>Skip hours of research across multiple apps and websites. MinuteTour eliminates the need to juggle between different platforms, saving you valuable time. Get a complete, optimized plan in seconds.</p>
        </div>
        <div class="benefit-image">
          <img src="../images/relaxing.svg" alt="Effortless planning" />
        </div>
      </div>
    </section>

    <!-- Dynamic & Personalized -->
    <section class="benefit-section benefit-reverse">
      <div class="benefit-content">
        <div class="benefit-text">
          <h3>Dynamic & Personalized Routes</h3>
          <p>Foodie, culture buff, nature lover? Your route adapts to your individual preferences. MinuteTour creates flexible routes tailored to what you love, ensuring every tour feels uniquely yours.</p>
        </div>
        <div class="benefit-image">
          <img src="../images/settings.svg" alt="Personalized routes" />
        </div>
      </div>
    </section>

    <!-- Time-Aware Exploration -->
    <section class="benefit-section">
      <div class="benefit-content">
        <div class="benefit-text">
          <h3>Time‑Aware Exploration</h3>
          <p>Tell us how long you have — whether it's 30 minutes or 3 hours. MinuteTour generates routes that fit perfectly into your available time, maximizing your experience without the stress of planning.</p>
        </div>
        <div class="benefit-image">
          <img src="../images/time-management.svg" alt="Time-aware exploration" />
        </div>
      </div>
    </section>

    <!-- Seamless Discovery -->
    <section class="benefit-section benefit-reverse">
      <div class="benefit-content">
        <div class="benefit-text">
          <h3>Seamless Discovery</h3>
          <p>All necessary POI information and navigation in one place — no tab juggling or app switching. Everything you need to explore confidently is right at your fingertips.</p>
        </div>
        <div class="benefit-image">
          <img src="../images/adventure.svg" alt="Seamless discovery" />
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section id="get-started" class="cta">
      <h2>Explore smarter. Anywhere. Anytime.</h2>
      <p>Join early users discovering cities with time‑aware, personalized routes.</p>
      <div class="cta-group cta-bottom">
        <a class="btn btn-secondary btn-download" href="#">Download (coming soon)</a>
        <router-link to="/app-demo" class="btn btn-primary">Try Web Demo</router-link>
      </div>
    </section>

    <footer class="footer">
      <p>© {{ new Date().getFullYear() }} MinuteTour — Smart, time‑aware city tours.</p>
    </footer>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Scroll animations using Intersection Observer
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in')
        observer.unobserve(entry.target)
      }
    })
  }, observerOptions)

  // Observe all benefit sections and other elements
  const elementsToAnimate = document.querySelectorAll('.benefit-section, .benefits-intro, .cta')
  elementsToAnimate.forEach(el => {
    observer.observe(el)
  })
})
</script>

<style scoped>
.landing {
  display: flex;
  flex-direction: column;
  background: linear-gradient(to bottom, #fafbfc 0%, #ffffff 100%);
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(50px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Scroll animations */
.benefit-section,
.benefits-intro,
.cta {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}

.benefit-section.animate-in,
.benefits-intro.animate-in,
.cta.animate-in {
  opacity: 1;
  transform: translateY(0);
}

.benefit-text,
.benefit-image {
  transition: opacity 0.8s ease-out 0.2s, transform 0.8s ease-out 0.2s;
}

.benefit-section.animate-in .benefit-text,
.benefit-section.animate-in .benefit-image {
  opacity: 1;
  transform: translateX(0);
}

/* Hero */
.hero {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 3rem;
  align-items: center;
  padding: 5rem 1.5rem 4rem;
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeIn 0.6s ease-out;
}
.hero-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.brand {
  margin: 0;
  font-size: 3.5rem;
  line-height: 1.1;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: fadeInUp 0.8s ease-out;
}
.tagline {
  margin: 0;
  font-size: 1.3rem;
  color: #555;
  line-height: 1.6;
  animation: fadeInUp 0.8s ease-out 0.2s both;
}
.cta-group {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
  animation: fadeInUp 0.8s ease-out 0.3s both;
}
.cta-bottom {
  justify-content: center;
}
.cta-bottom .btn {
  min-width: auto;
  max-width: 200px;
}
.btn-download {
  min-width: 220px;
  max-width: 220px;
  white-space: nowrap;
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.875rem 1.75rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95rem;
  border: 1px solid transparent;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-decoration: none;
  cursor: pointer;
  min-width: 140px;
}
.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.3);
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}
.btn-secondary {
  background: #fff;
  color: #111;
  border: 2px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.btn-secondary:hover {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.btn-ghost {
  background: transparent;
  color: #111;
  border-color: #ddd;
}
.btn-ghost:hover { border-color: #bbb; }

.hero-badges {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
  animation: fadeInUp 0.8s ease-out 0.4s both;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 0.625rem 1rem;
  border-radius: 999px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  color: #333;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.badge:hover {
  transform: translateY(-2px);
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}
.icon {
  width: 18px;
  height: 18px;
}
.hero-visual {
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.8s ease-out 0.5s both;
}
.device-mockup {
  position: relative;
  width: min(520px, 90%);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}
.device-mockup:hover {
  transform: scale(1.02);
}
.mock-map {
  width: 100%;
  max-width: 500px;
  height: auto;
  display: block;
}

/* Benefits Intro */
.benefits-intro {
  padding: 5rem 1.5rem 3rem;
  text-align: center;
  max-width: 1200px;
  margin: 0 auto;
}
.benefits-intro h2 {
  margin: 0;
  font-size: 2.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  letter-spacing: -0.02em;
}

/* Benefit Sections */
.benefit-section {
  padding: 5rem 1.5rem;
  background: #fff;
  position: relative;
  overflow: hidden;
}
.benefit-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.2), transparent);
}
.benefit-section:nth-child(even) {
  background: linear-gradient(to bottom, #fafbfc 0%, #ffffff 100%);
}
.benefit-section:first-of-type {
  background: #fff;
}
.benefit-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
}
.benefit-reverse .benefit-content {
  direction: rtl;
}
.benefit-reverse .benefit-content > * {
  direction: ltr;
}
.benefit-text {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  opacity: 0;
  transform: translateX(-50px);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}
.benefit-reverse .benefit-text {
  transform: translateX(50px);
}
.benefit-text h3 {
  margin: 0;
  font-size: 2.25rem;
  color: #111;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.benefit-text p {
  margin: 0;
  font-size: 1.15rem;
  line-height: 1.8;
  color: #555;
}
.benefit-image {
  width: 100%;
  height: 450px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  opacity: 0;
  transform: translateX(50px);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}
.benefit-reverse .benefit-image {
  transform: translateX(-50px);
}
.benefit-image:hover {
  transform: translateX(0) scale(1.05);
}
.benefit-reverse .benefit-image:hover {
  transform: translateX(0) scale(1.05);
}
.benefit-image img {
  width: 100%;
  max-width: 450px;
  height: auto;
  display: block;
  transition: transform 0.3s ease;
}
.benefit-image:hover img {
  transform: scale(1.05);
}

/* CTA */
.cta {
  padding: 5rem 1.5rem 4rem;
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  position: relative;
  overflow: hidden;
}
.cta::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  animation: pulse 4s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 0.8; }
}
.cta h2 {
  margin: 0 0 0.75rem 0;
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  position: relative;
  z-index: 1;
}
.cta p {
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 2rem 0;
  font-size: 1.2rem;
  position: relative;
  z-index: 1;
}

/* Footer */
.footer {
  padding: 3rem 1.5rem;
  text-align: center;
  color: #777;
  background: #fafbfc;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

/* Responsive */
@media (max-width: 960px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 3rem 1.5rem 2rem;
    gap: 2rem;
  }
  .brand {
    font-size: 2.5rem;
  }
  .tagline {
    font-size: 1.15rem;
  }
  .benefit-content {
    grid-template-columns: 1fr;
    gap: 2.5rem;
  }
  .benefit-reverse .benefit-content {
    direction: ltr;
  }
  .benefit-text,
  .benefit-reverse .benefit-text {
    transform: translateY(30px);
  }
  .benefit-section.animate-in .benefit-text,
  .benefit-section.animate-in .benefit-reverse .benefit-text {
    transform: translateY(0);
  }
  .benefit-image,
  .benefit-reverse .benefit-image {
    transform: translateY(30px);
  }
  .benefit-section.animate-in .benefit-image,
  .benefit-section.animate-in .benefit-reverse .benefit-image {
    transform: translateY(0);
  }
  .benefit-image {
    height: 320px;
  }
  .benefits-intro {
    padding: 4rem 1.5rem 2rem;
  }
  .benefits-intro h2 {
    font-size: 2.25rem;
  }
  .benefit-text h3 {
    font-size: 1.875rem;
  }
  .cta h2 {
    font-size: 2rem;
  }
}
@media (max-width: 600px) {
  .hero {
    padding: 2.5rem 1.5rem 1.5rem;
  }
  .brand {
    font-size: 2rem;
  }
  .tagline {
    font-size: 1.05rem;
  }
  .btn {
    padding: 0.75rem 1.5rem;
    font-size: 0.9rem;
    min-width: 120px;
  }
  .benefit-section {
    padding: 3.5rem 1.5rem;
  }
  .benefit-text h3 {
    font-size: 1.625rem;
  }
  .benefit-text p {
    font-size: 1.05rem;
  }
  .benefit-image {
    height: 280px;
  }
  .cta {
    padding: 4rem 1.5rem 3rem;
  }
  .cta h2 {
    font-size: 1.75rem;
  }
  .cta p {
    font-size: 1.05rem;
  }
  .cta-group {
    flex-direction: column;
    align-items: center;
  }
  .cta-bottom .btn {
    width: 100%;
    max-width: 250px;
  }
  .benefits-intro {
    padding: 3rem 1.5rem 1.5rem;
  }
  .benefits-intro h2 {
    font-size: 1.875rem;
  }
}
</style>
