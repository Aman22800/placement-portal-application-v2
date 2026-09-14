<template>
  <div class="container" style="max-width: 480px; margin-top: 80px;">
    <h2 class="mb-4 text-center">Placement Portal</h2>

    <div v-if="message" class="alert alert-danger">{{ message }}</div>

    <div class="mb-3">
      <label class="form-label">Email</label>
      <input type="email" class="form-control" v-model="email">
    </div>
    <div class="mb-3">
      <label class="form-label">Password</label>
      <input type="password" class="form-control" v-model="password">
    </div>
    <button class="btn btn-primary w-100 mb-3" @click="login">Login</button>

    <div class="text-center">
      <router-link to="/register/student">Register as Student</router-link>
      &nbsp;|&nbsp;
      <router-link to="/register/company">Register as Company</router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Login',
  data() {
    return {
      email: '',
      password: '',
      message: ''
    }
  },
  methods: {
    async login() {
      this.message = ''
      try {
        const res = await axios.post('/api/login', {
          email: this.email,
          password: this.password
        })

        // Save token + role so other pages can use them
        sessionStorage.setItem('token', res.data.access_token)
        sessionStorage.setItem('role', res.data.role)

        // Redirect based on role
        this.$router.push(`/${res.data.role}/dashboard`)

      } catch (err) {
        // axios throws on non-2xx responses -- the actual error message
        // from Flask lives in err.response.data.error
        this.message = err.response?.data?.error || 'Login failed'
      }
    }
  }
}
</script>