const API_BASE = 'http://127.0.0.1:5000';

const getToken = () => localStorage.getItem('kc_token');
const getUser  = () => JSON.parse(localStorage.getItem('kc_user') || 'null');

function requireAuth() {
  if (!getToken()) window.location.href = getBasePath() + 'pages/login.html';
}
function requireVendor() {
  const u = getUser();
  if (!getToken() || !u || !['vendor','admin'].includes(u.role))
    window.location.href = getBasePath() + 'pages/login.html';
}
function getBasePath() {
  const p = window.location.pathname;
  return p.includes('/pages/') ? '../' : './';
}

async function apiCall(endpoint, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);
  try {
    const res  = await fetch(API_BASE + endpoint, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.msg || 'Something went wrong');
    return data;
  } catch(e) {
    if (e.name === 'TypeError') throw new Error('Cannot connect to server. Is the backend running?');
    throw e;
  }
}

const Auth = {
  signup:  d => apiCall('/auth/signup', 'POST', d),
  login:   d => apiCall('/auth/login',  'POST', d),
  profile: () => apiCall('/auth/profile'),
  update:  d => apiCall('/auth/profile', 'PUT', d),
  logout:  () => { localStorage.clear(); window.location.href = getBasePath() + 'index.html'; }
};

const Orders = {
  place:        d      => apiCall('/orders/place', 'POST', d),
  my:           ()     => apiCall('/orders/my'),
  detail:       id     => apiCall(`/orders/${id}`),
  cancel:       id     => apiCall(`/orders/${id}/cancel`, 'PUT'),
  review:       (id,d) => apiCall(`/orders/${id}/review`, 'POST', d),
  createPayment:id     => apiCall(`/orders/${id}/create-payment`, 'POST'),
  verifyPayment:(id,d) => apiCall(`/orders/${id}/verify-payment`, 'POST', d),
};

const Vendor = {
  allOrders:    s      => apiCall(`/vendor/orders${s?'?status='+s:''}`),
  updateStatus: (id,d) => apiCall(`/vendor/orders/${id}/status`, 'PUT', d),
  assignSub:    (id,d) => apiCall(`/vendor/suborders/${id}/assign`, 'PUT', d),
  dashboard:    ()     => apiCall('/vendor/dashboard'),
};

const Partner = {
  register: d => apiCall('/partner/register', 'POST', d),
  myJobs:   () => apiCall('/partner/my-jobs'),
  updateJob:(id,d) => apiCall(`/partner/jobs/${id}/status`, 'PUT', d),
  all:      () => apiCall('/partner/all'),
};

const Admin = {
  users:      () => apiCall('/admin/users'),
  analytics:  () => apiCall('/admin/analytics'),
  toggleUser: id => apiCall(`/admin/users/${id}/toggle`, 'PUT'),
  changeRole: (id,d) => apiCall(`/admin/users/${id}/role`, 'PUT', d),
};