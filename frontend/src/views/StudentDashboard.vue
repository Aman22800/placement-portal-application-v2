<template>
  <div class="container mt-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Student Dashboard</h2>
      <button class="btn btn-outline-secondary btn-sm" @click="logout">Logout</button>
    </div>

    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <a class="nav-link" :class="{active: tab === 'drives'}" href="#" @click.prevent="tab = 'drives'">Eligible Drives</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: tab === 'applications'}" href="#" @click.prevent="tab = 'applications'">My Applications</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" :class="{active: tab === 'profile'}" href="#" @click.prevent="tab = 'profile'; fetchProfile()">My Profile</a>
      </li>
    </ul>

    <div v-if="message" class="alert" :class="messageType === 'error' ? 'alert-danger' : 'alert-success'">
      {{ message }}
    </div>

    <!-- ELIGIBLE DRIVES TAB -->
    <div v-if="tab === 'drives'">
      <div v-if="drives.length === 0" class="text-muted">No eligible drives available right now.</div>
      <div class="card mb-3" v-for="drive in drives" :key="drive.id">
        <div class="card-body">
          <h5 class="card-title">{{ drive.job_title }}</h5>
          <p class="card-text">{{ drive.job_description }}</p>
          <p class="card-text">
            <small class="text-muted">
              Branch: {{ drive.eligibility_branch }} | Min CGPA: {{ drive.eligibility_min_cgpa }} |
              Deadline: {{ drive.application_deadline }}
            </small>
          </p>
          <button class="btn btn-primary btn-sm" @click="applyToDrive(drive.id)">Apply</button>
        </div>
      </div>
    </div>

    <!-- MY APPLICATIONS TAB -->
    <div v-if="tab === 'applications'">
      <table class="table">
        <thead>
          <tr>
            <th>Job Title</th>
            <th>Status</th>
            <th>Interview</th>
            <th>Offer Salary</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="app in applications" :key="app.application_id">
            <td>{{ app.job_title }}</td>
            <td>{{ app.status }}</td>
            <td>{{ app.interview_datetime || '-' }}</td>
            <td>{{ app.offer_salary || '-' }}</td>
            <td>
              <button v-if="app.status === 'Selected'" class="btn btn-success btn-sm"
                      @click="acceptOffer(app.application_id)">
                Accept Offer
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- MY PROFILE TAB -->
    <div v-if="tab === 'profile'" style="max-width: 500px;">
      <div class="mb-3">
        <label class="form-label">Name</label>
        <input type="text" class="form-control" :value="profile.name" disabled>
        <small class="text-muted">Name cannot be changed after registration.</small>
      </div>
      <div class="mb-3">
        <label class="form-label">Email</label>
        <input type="text" class="form-control" :value="profile.email" disabled>
      </div>
      <div class="mb-3">
        <label class="form-label">Branch</label>
        <input type="text" class="form-control" v-model="profileForm.branch">
      </div>
      <div class="mb-3">
        <label class="form-label">CGPA</label>
        <input type="number" step="0.1" class="form-control" v-model.number="profileForm.cgpa">
      </div>
      <div class="mb-3">
        <label class="form-label">Graduation Year</label>
        <input type="number" class="form-control" v-model.number="profileForm.year">
      </div>
      <div class="mb-3">
        <label class="form-label">Skills (comma-separated)</label>
        <input type="text" class="form-control" v-model="profileForm.skills" placeholder="Python, SQL, React">
      </div>
      <button class="btn btn-primary mb-4" @click="saveProfile">Save Profile</button>

      <hr>

      <h5>Resume</h5>
      <p v-if="profile.resume_uploaded" class="text-success">
        A resume is already on file.
        <a href="#" @click.prevent="downloadOwnResume">Download it</a>
      </p>
      <p v-else class="text-muted">No resume uploaded yet.</p>

      <div class="mb-2">
        <input type="file" class="form-control" ref="resumeFile" accept=".pdf,.doc,.docx">
      </div>
      <button class="btn btn-outline-primary" @click="uploadResume">Upload Resume</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'StudentDashboard',
  data() {
    return {
      tab: 'drives',
      drives: [],
      applications: [],
      profile: {},
      profileForm: { branch: '', cgpa: null, year: null, skills: '' },
      message: '',
      messageType: 'error'
    }
  },
  mounted() {
    this.fetchDrives()
    this.fetchApplications()
  },
  methods: {
    authHeader() {
      return { headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}` } }
    },

    async fetchDrives() {
      try {
        const res = await axios.get('/api/student/drives', this.authHeader())
        this.drives = res.data
      } catch (err) {
        this.message = 'Could not load drives'
        this.messageType = 'error'
      }
    },

    async fetchApplications() {
      try {
        const res = await axios.get('/api/student/applications', this.authHeader())
        this.applications = res.data
      } catch (err) {
        this.message = 'Could not load applications'
        this.messageType = 'error'
      }
    },

    async applyToDrive(driveId) {
      this.message = ''
      try {
        await axios.post(`/api/student/drives/${driveId}/apply`, {}, this.authHeader())
        this.message = 'Applied successfully!'
        this.messageType = 'success'
        this.fetchApplications()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not apply'
        this.messageType = 'error'
      }
    },

    async acceptOffer(applicationId) {
      this.message = ''
      try {
        await axios.put(`/api/student/applications/${applicationId}/accept-offer`, {}, this.authHeader())
        this.message = 'Offer accepted!'
        this.messageType = 'success'
        this.fetchApplications()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not accept offer'
        this.messageType = 'error'
      }
    },

    // ---------- PROFILE METHODS ----------
    async fetchProfile() {
      try {
        const res = await axios.get('/api/student/profile', this.authHeader())
        this.profile = res.data
        // pre-fill the editable form with current values
        this.profileForm.branch = res.data.branch
        this.profileForm.cgpa = res.data.cgpa
        this.profileForm.year = res.data.year
        this.profileForm.skills = res.data.skills || ''
      } catch (err) {
        this.message = 'Could not load profile'
        this.messageType = 'error'
      }
    },

    async saveProfile() {
      this.message = ''
      try {
        await axios.put('/api/student/profile', this.profileForm, this.authHeader())
        this.message = 'Profile updated successfully!'
        this.messageType = 'success'
        this.fetchProfile()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not update profile'
        this.messageType = 'error'
      }
    },

    async uploadResume() {
      this.message = ''
      const file = this.$refs.resumeFile.files[0]
      if (!file) {
        this.message = 'Please choose a file first'
        this.messageType = 'error'
        return
      }

      // File uploads need FormData, not a plain JSON body
      const formData = new FormData()
      formData.append('resume', file)

      try {
        await axios.post('/api/student/profile/resume', formData, {
          headers: {
            Authorization: `Bearer ${sessionStorage.getItem('token')}`,
            'Content-Type': 'multipart/form-data'
          }
        })
        this.message = 'Resume uploaded successfully!'
        this.messageType = 'success'
        this.fetchProfile()
      } catch (err) {
        this.message = err.response?.data?.error || 'Could not upload resume'
        this.messageType = 'error'
      }
    },

    async downloadOwnResume() {
      try {
        const res = await axios.get('/api/student/profile/resume', {
          ...this.authHeader(),
          responseType: 'blob'  // tells axios to expect binary file data, not JSON
        })
        // Pull the real filename (with its correct extension) out of the
        // Content-Disposition header the server sends, instead of hardcoding
        // one -- hardcoding 'resume' with no extension is what caused the
        // browser to save it as unreadable garbage before.
        const disposition = res.headers['content-disposition'] || ''
        const match = disposition.match(/filename="?([^"]+)"?/)
        const filename = match ? match[1] : 'resume.pdf'

        const url = window.URL.createObjectURL(new Blob([res.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
      } catch (err) {
        this.message = 'Could not download resume'
        this.messageType = 'error'
      }
    },

    logout() {
      sessionStorage.clear()
      this.$router.push('/')
    }
  }
}
</script>