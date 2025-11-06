<template>
  <div class="pricing-page">
    <!-- Hero Section -->
    <section class="pricing-hero">
      <div class="pricing-hero-content">
        <h1 class="pricing-title">Choose Your Plan</h1>
        <p class="pricing-tagline">
          Start exploring cities with our free plan, or unlock unlimited adventures with Pro. 
          All plans include our smart route planning and personalized recommendations.
        </p>
      </div>
    </section>

    <!-- Pricing Cards -->
    <section class="pricing-section">
      <div class="pricing-cards">
        <!-- Free Plan -->
        <div class="pricing-card">
          <div class="plan-header">
            <h3 class="plan-name">Free</h3>
            <div class="plan-price">
              <span class="price-amount">$0</span>
              <span class="price-period">/month</span>
            </div>
          </div>
          <div class="plan-features">
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>10 guided hours per month</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Personalized route planning</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Time-aware exploration</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>POI information & navigation</span>
            </div>
          </div>
          <router-link to="/app-demo" class="btn btn-plan btn-free">Try Demo</router-link>
        </div>

        <!-- Pro Plan -->
        <div class="pricing-card pricing-card-pro">
          <div class="plan-header">
            <h3 class="plan-name">Pro</h3>
            <div class="plan-price">
              <span class="price-amount">X</span>
              <span class="price-period">/month</span>
            </div>
          </div>
          <div class="plan-features">
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span><strong>Unlimited</strong> guided hours</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Advanced personalized routes</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Advanced POI filters</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              <span>Route history & favorites</span>
            </div>
          </div>
          <button class="btn btn-plan btn-pro" disabled>Coming Soon</button>
        </div>
      </div>
    </section>

    <!-- FAQ Section -->
    <section class="faq-section">
      <div class="faq-content">
        <h2>Frequently Asked Questions</h2>
        <div class="faq-grid">
          <div class="faq-item">
            <h4>What counts as a guided hour?</h4>
            <p>A guided hour is any time you spend actively using MinuteTour to navigate a route. Paused tours or time spent browsing don't count toward your limit.</p>
          </div>
          <div class="faq-item">
            <h4>Can I upgrade or downgrade anytime?</h4>
            <p>Yes! You can change your plan at any time. Upgrades take effect immediately, and downgrades take effect at the start of your next billing cycle.</p>
          </div>
          <div class="faq-item">
            <h4>What happens if I exceed my free hours?</h4>
            <p>You'll receive a notification when you're approaching your limit. You can either upgrade to Pro or wait until the next month when your hours reset.</p>
          </div>
          <div class="faq-item">
            <h4>Do you offer refunds?</h4>
            <p>We offer a 30-day money-back guarantee for Pro subscriptions. If you're not satisfied, contact us for a full refund.</p>
          </div>
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

  const elementsToAnimate = document.querySelectorAll('.pricing-card, .faq-item')
  elementsToAnimate.forEach(el => {
    observer.observe(el)
  })
})
</script>

<style scoped>
.pricing-page {
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

/* Pricing Hero */
.pricing-hero {
  padding: 5rem 1.5rem 3rem;
  text-align: center;
  max-width: 800px;
  margin: 0 auto;
  animation: fadeInUp 0.8s ease-out;
}

.pricing-title {
  margin: 0 0 1rem 0;
  font-size: 3.5rem;
  line-height: 1.1;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.pricing-tagline {
  margin: 0;
  font-size: 1.3rem;
  color: #555;
  line-height: 1.8;
}

/* Pricing Section */
.pricing-section {
  padding: 3rem 1.5rem 5rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.pricing-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 2rem;
  max-width: 900px;
  margin: 0 auto;
}

.pricing-card {
  background: #fff;
  border-radius: 20px;
  padding: 2.5rem;
  border: 2px solid #e5e7eb;
  position: relative;
  transition: all 0.3s ease;
  opacity: 0;
  transform: translateY(30px);
}

.pricing-card.animate-in {
  opacity: 1;
  transform: translateY(0);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}

.pricing-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(102, 126, 234, 0.15);
}

.pricing-card-pro {
  border-color: #667eea;
  background: linear-gradient(to bottom, #fff 0%, #fafbfc 100%);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
}


.plan-header {
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.plan-name {
  margin: 0 0 1rem 0;
  font-size: 2rem;
  font-weight: 700;
  color: #111;
}

.plan-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.5rem;
}

.price-amount {
  font-size: 3rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.price-period {
  font-size: 1.1rem;
  color: #777;
}

.plan-features {
  margin-bottom: 5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-size: 1rem;
  color: #555;
  line-height: 1.6;
}

.feature-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  margin-top: 2px;
  color: #667eea;
}

.btn-plan {
  display: block;
  width: 100%;
  padding: 0.5rem 2rem 1.5rem;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  text-align: center;
  text-decoration: none;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  cursor: pointer;
  font-family: inherit;
  line-height: 1.5;
  margin: 0;
}

.btn-free {
  background: #fff;
  color: #111;
  border-color: #e5e7eb;
}

.btn-free:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-free:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #f5f5f5;
  color: #999;
}

.btn-pro {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.3);
}

.btn-pro:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-pro:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: linear-gradient(135deg, #a0aec0 0%, #b8b8b8 100%);
  box-shadow: none;
}

/* FAQ Section */
.faq-section {
  padding: 5rem 1.5rem;
  background: linear-gradient(to bottom, #fafbfc 0%, #ffffff 100%);
}

.faq-content {
  max-width: 1000px;
  margin: 0 auto;
}

.faq-content h2 {
  text-align: center;
  margin: 0 0 3rem 0;
  font-size: 2.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.faq-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}

.faq-item {
  background: #fff;
  padding: 2rem;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.8s ease-out, transform 0.8s ease-out;
}

.faq-item.animate-in {
  opacity: 1;
  transform: translateY(0);
}

.faq-item h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1.25rem;
  color: #111;
  font-weight: 600;
}

.faq-item p {
  margin: 0;
  color: #555;
  line-height: 1.7;
}

/* Responsive */
@media (max-width: 960px) {
  .pricing-title {
    font-size: 2.5rem;
  }
  .pricing-tagline {
    font-size: 1.15rem;
  }
  .pricing-cards {
    grid-template-columns: 1fr;
    max-width: 500px;
  }
  .faq-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .pricing-hero {
    padding: 3rem 1.5rem 2rem;
  }
  .pricing-title {
    font-size: 2rem;
  }
  .pricing-tagline {
    font-size: 1.05rem;
  }
  .pricing-card {
    padding: 2rem;
  }
  .price-amount {
    font-size: 2.5rem;
  }
  .faq-content h2 {
    font-size: 2rem;
  }
}
</style>

