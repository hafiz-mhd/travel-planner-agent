import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const createUser = (data) => api.post('/users', data)
export const getUser = (id) => api.get(`/users/${id}`)
export const generateItinerary = (data) => api.post('/generate-itinerary', data)
export const refineItinerary = (data) => api.post('/refine-itinerary', data)
export const getTrips = (userId) => api.get(`/get-trips/${userId}`)
export const getTrip = (id) => api.get(`/trips/${id}`)
export const deleteTrip = (id) => api.delete(`/trips/${id}`)
export const getWeather = (city, start, end) =>
  api.get('/weather', { params: { city, start_date: start, end_date: end } })

export default api
