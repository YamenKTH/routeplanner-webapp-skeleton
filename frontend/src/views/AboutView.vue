<template>
  <div class="about-page">
    <!-- Hero Section -->
    <section class="about-hero">
      <div class="about-hero-content">
        <h1 class="about-title">Meet Our Team</h1>
        <p class="about-tagline">
          We're a passionate team of five engineers dedicated to transforming how people explore cities. 
          Combining data science, city planning, and innovative technology, we're building the future of 
          personalized travel experiences.
        </p>
      </div>
    </section>

    <!-- Team Image Section -->
    <section class="team-image-section">
      <div class="team-image-container">
        <img src="../images/aboutUs.png" alt="MinuteTour Team" class="team-image" />
      </div>
    </section>

    <!-- Our Story Section -->
    <section class="story-section">
      <div class="story-content">
        <h2>Our Story</h2>
        <div class="story-text">
          <p>
            MinuteTour was born from a simple frustration: planning city tours shouldn't be complicated. 
            As engineers passionate about sustainable design and urban exploration, we recognized that 
            existing solutions were either too rigid or required hours of research.
          </p>
          <p>
            Our team of five brings together expertise in data science, city planning, software engineering, 
            and user experience design. We've combined our diverse backgrounds to create an intelligent 
            platform that understands both the technical complexity of route optimization and the human 
            desire for spontaneous discovery.
          </p>
          <p>
            What drives us is the belief that technology should enhance, not complicate, the joy of 
            exploration. Every feature we build, every algorithm we refine, is designed with one goal: 
            to help people discover cities effortlessly, making every moment count.
          </p>
        </div>
      </div>
    </section>

    <!-- Values Section -->
    <section class="values-section">
      <div class="values-content">
        <h2>What We Value</h2>
        <div class="values-grid">
          <div class="value-card">
            <div class="value-icon">🎯</div>
            <h3>Innovation</h3>
            <p>We're constantly pushing boundaries, combining cutting-edge technology with practical solutions that make a real difference in people's lives.</p>
          </div>
          <div class="value-card">
            <div class="value-icon">🌍</div>
            <h3>Sustainability</h3>
            <p>We believe in sustainable exploration that respects cities and communities while promoting walking and eco-friendly travel.</p>
          </div>
          <div class="value-card">
            <div class="value-icon">👥</div>
            <h3>User-Centric</h3>
            <p>Every decision we make starts with our users. We listen, learn, and iterate to create experiences that truly serve travelers.</p>
          </div>
          <div class="value-card">
            <div class="value-icon">🔬</div>
            <h3>Data-Driven</h3>
            <p>We combine rich data insights with intelligent algorithms to deliver personalized experiences that adapt to each user's unique needs.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="about-cta">
      <div class="about-cta-content">
        <h2>Join Us on This Journey</h2>
        <p>We're just getting started. Join thousands of explorers who are discovering cities in a whole new way.</p>
        <div class="cta-buttons">
          <router-link to="/app-demo" class="btn btn-primary">Try the Demo</router-link>
          <router-link to="/vision" class="btn btn-secondary">View Pricing</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Scroll animations
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

  const elementsToAnimate = document.querySelectorAll('.value-card, .story-section, .team-image-section')
  elementsToAnimate.forEach(el => {
    observer.observe(el)
  })
})
</script>

<style scoped>
.about-page {
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

/* About Hero */
.about-hero {
  padding: 5rem 1.5rem 3rem;
  text-align: center;
  max-width: 900px;
  margin: 0 auto;
  animation: fadeInUp 0.8s ease-out;
}

.about-title {
  margin: 0 0 1rem 0;
  font-size: 3.5rem;
  line-height: 1.1;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.about-tagline {
  margin: 0;
  font-size: 1.3rem;
  color: #555;
  line-height: 1.8;
}

/* Team Image Section */
.team-image-section {
  padding: 2rem 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
  background: #fff;
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}

.team-image-section.animate-in {
  opacity: 1;
  transform: translateY(0);
}

.team-image-container {
  width: 100%;
  overflow: hidden;
}

.team-image {
  width: 100%;
  height: auto;
  display: block;
}

/* Story Section */
.story-section {
  padding: 5rem 1.5rem;
  max-width: 900px;
  margin: 0 auto;
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}

.story-section.animate-in {
  opacity: 1;
  transform: translateY(0);
}

.story-content h2 {
  margin: 0 0 2rem 0;
  font-size: 2.5rem;
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.story-text {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.story-text p {
  margin: 0;
  font-size: 1.15rem;
  line-height: 1.8;
  color: #555;
}

/* Values Section */
.values-section {
  padding: 5rem 1.5rem;
  background: linear-gradient(to bottom, #fafbfc 0%, #ffffff 100%);
}

.values-content {
  max-width: 1200px;
  margin: 0 auto;
}

.values-content h2 {
  text-align: center;
  margin: 0 0 3rem 0;
  font-size: 2.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.values-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.value-card {
  background: #fff;
  padding: 2.5rem;
  border-radius: 20px;
  border: 1px solid #e5e7eb;
  text-align: center;
  transition: all 0.3s ease;
  opacity: 0;
  transform: translateY(30px);
}

.value-card.animate-in {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}

.value-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 30px rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.3);
}

.value-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.value-card h3 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  color: #111;
  font-weight: 700;
}

.value-card p {
  margin: 0;
  color: #555;
  line-height: 1.7;
  font-size: 1rem;
}

/* About CTA */
.about-cta {
  padding: 5rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.about-cta::before {
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

.about-cta-content {
  max-width: 700px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.about-cta h2 {
  margin: 0 0 1rem 0;
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.about-cta p {
  margin: 0 0 2rem 0;
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.8;
}

.cta-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.875rem 1.75rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.btn-primary {
  background: #fff;
  color: #667eea;
  box-shadow: 0 4px 14px rgba(255, 255, 255, 0.2);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 255, 255, 0.3);
}

.btn-secondary {
  background: transparent;
  color: white;
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-secondary:hover {
  border-color: rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.1);
}

/* Responsive */
@media (max-width: 960px) {
  .about-title {
    font-size: 2.5rem;
  }
  .about-tagline {
    font-size: 1.15rem;
  }
  .values-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .story-content h2 {
    font-size: 2rem;
  }
  .about-cta h2 {
    font-size: 2rem;
  }
}

@media (max-width: 600px) {
  .about-hero {
    padding: 3rem 1.5rem 2rem;
  }
  .about-title {
    font-size: 2rem;
  }
  .about-tagline {
    font-size: 1.05rem;
  }
  .values-grid {
    grid-template-columns: 1fr;
  }
  .value-card {
    padding: 2rem;
  }
  .story-text p {
    font-size: 1.05rem;
  }
  .about-cta {
    padding: 4rem 1.5rem;
  }
  .about-cta h2 {
    font-size: 1.75rem;
  }
  .about-cta p {
    font-size: 1.05rem;
  }
  .cta-buttons {
    flex-direction: column;
    align-items: stretch;
  }
  .btn {
    width: 100%;
  }
}
</style>
