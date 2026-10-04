(() => {
  const walletButton = document.getElementById('wallet');
  const loginDialog = document.createElement('dialog');
  let student = null;
  let signedIn = false;
  let documents = [];

  const loginStyle = document.createElement('style');
  loginStyle.textContent = `
    #lockerLogin { width: min(420px, calc(100% - 32px)); padding: 0; border: 1px solid #e5e7eb; border-radius: 12px; color: #172033; background: #fff; }
    #lockerLogin::backdrop { background: rgba(11, 18, 32, .55); }
    #lockerLogin form { padding: 24px; }
    #lockerLogin h2 { margin: 0 0 18px; }
    #lockerLogin label { display: block; margin: 14px 0 6px; font-size: 14px; }
    #lockerLogin input { width: 100%; padding: 11px; border: 1px solid #d1d5db; border-radius: 7px; }
    #lockerLogin .login-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }
    #lockerLogin .login-error { min-height: 20px; color: #b42318; font-size: 13px; }
  `;
  document.head.append(loginStyle);

  loginDialog.id = 'lockerLogin';
  loginDialog.innerHTML = `
    <form>
      <h2>Sign in to your student account</h2>
      <label for="lockerUsername">Username</label>
      <input id="lockerUsername" name="username" autocomplete="username" required>
      <label for="lockerPassword">Password</label>
      <input id="lockerPassword" name="password" type="password" autocomplete="current-password" required>
      <p class="login-error" role="status" aria-live="polite"></p>
      <div class="login-actions">
        <button class="btn" type="button" data-login-close>Cancel</button>
        <button class="btn primary" type="submit">Sign in</button>
      </div>
    </form>
  `;
  document.body.append(loginDialog);

  function csrfToken() {
    const cookie = document.cookie.split('; ').find(value => value.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.slice('csrftoken='.length)) : '';
  }

  async function requestJson(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      credentials: 'same-origin',
      headers: {
        Accept: 'application/json',
        ...(options.headers || {})
      }
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'The request could not be completed.');
    return data;
  }

  function makeRow(title, detail) {
    const row = document.createElement('div');
    row.className = 'mini';
    const label = document.createElement('span');
    label.textContent = title;
    const value = document.createElement('span');
    value.className = 'pill';
    value.textContent = detail;
    row.append(label, value);
    return row;
  }

  function formatDate(value) {
    return new Date(value).toLocaleDateString();
  }

  function renderDocuments() {
    const dashboard = document.querySelector('#dashboard .profile');
    const identity = document.querySelector('#profile .profile');
    const heading = dashboard.querySelector('h2');
    const dashboardDetails = dashboard.querySelectorAll('p');
    heading.textContent = student.name;
    dashboardDetails[0].textContent = `${student.student_id} · ${student.course}`;
    dashboardDetails[1].textContent = `${student.email} · Academic year ${student.year}`;

    const identityHeading = identity.querySelector('h2');
    const identityDetails = identity.querySelectorAll('p');
    identityHeading.textContent = student.name;
    identityDetails[0].textContent = `Student ID: ${student.student_id}`;
    identityDetails[1].textContent = student.course;
    identityDetails[2].textContent = `Email: ${student.email} · Academic year ${student.year}`;

    const counts = document.querySelectorAll('#dashboard .stats .stat strong');
    const academicCount = documents.filter(record => record.document_type.toLowerCase().includes('mark')).length;
    const courseCount = student.course ? 1 : 0;
    const certificateCount = documents.filter(record =>
      ['certificate', 'bonafide', 'internship'].some(type => record.document_type.toLowerCase().includes(type))
    ).length;
    counts[0].textContent = academicCount;
    counts[1].textContent = courseCount;
    counts[2].textContent = certificateCount;
    counts[3].textContent = '0';

    const timeline = document.querySelector('#dashboard .timeline');
    timeline.replaceChildren();
    documents.slice(0, 5).forEach(record => {
      const item = document.createElement('div');
      item.className = 'item';
      const title = document.createElement('b');
      title.textContent = record.original_filename || record.document_type;
      const status = document.createElement('span');
      status.className = 'pill';
      status.textContent = record.status;
      const details = document.createElement('p');
      details.textContent = `${record.document_type} · ${formatDate(record.uploaded_at)}`;
      item.append(title, status, details);
      timeline.append(item);
    });
    if (!documents.length) timeline.textContent = 'No documents have been issued to this student yet.';

    const table = document.querySelector('#academic .table');
    table.querySelector('tr').replaceChildren(...['Document', 'Record ID', 'Status', 'File'].map(text => {
      const cell = document.createElement('th');
      cell.textContent = text;
      return cell;
    }));
    table.querySelectorAll('tr:not(:first-child)').forEach(row => row.remove());
    documents.forEach(record => {
      const row = document.createElement('tr');
      [record.original_filename || record.document_type, record.document_id, record.status].forEach(text => {
        const cell = document.createElement('td');
        cell.textContent = text;
        row.append(cell);
      });
      const fileCell = document.createElement('td');
      if (record.file_url) {
        const link = document.createElement('a');
        link.href = record.file_url;
        link.textContent = 'Download';
        fileCell.append(link);
      } else {
        fileCell.textContent = 'Unavailable';
      }
      row.append(fileCell);
      table.append(row);
    });
    if (!documents.length) {
      const row = document.createElement('tr');
      const cell = document.createElement('td');
      cell.colSpan = 4;
      cell.textContent = 'No academic records are available.';
      row.append(cell);
      table.append(row);
    }

    const courseList = document.querySelector('#courses .card');
    courseList.querySelectorAll('.mini').forEach(row => row.remove());
    courseList.append(makeRow(student.course, `Year ${student.year}`));

    const certificates = document.querySelector('#certificates .card');
    certificates.querySelectorAll('.mini').forEach(row => row.remove());
    documents
      .filter(record => ['certificate', 'bonafide', 'internship'].some(type => record.document_type.toLowerCase().includes(type)))
      .forEach(record => certificates.append(makeRow(record.original_filename || record.document_type, record.status)));
    if (!certificates.querySelector('.mini')) certificates.append(makeRow('No certificates issued', 'None'));

    const achievements = document.querySelector('#activities .card');
    achievements.querySelectorAll('.mini').forEach(row => row.remove());
    achievements.append(makeRow('No achievement records are linked to the student account', 'None'));
  }

  async function loadLocker() {
    const data = await requestJson('/api/student-locker/');
    student = data.student;
    documents = data.documents;
    renderDocuments();
  }

  walletButton.onclick = () => {
    if (signedIn) {
      requestJson('/api/logout/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken() }
      }).then(() => window.location.reload()).catch(error => {
        loginDialog.querySelector('.login-error').textContent = error.message;
      });
      return;
    }
    loginDialog.showModal();
    loginDialog.querySelector('#lockerUsername').focus();
  };

  loginDialog.querySelector('[data-login-close]').addEventListener('click', () => loginDialog.close());
  loginDialog.querySelector('form').addEventListener('submit', async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const errorMessage = loginDialog.querySelector('.login-error');
    const credentials = new URLSearchParams(new FormData(form));
    try {
      await requestJson('/api/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken()
        },
        body: credentials
      });
      signedIn = true;
      walletButton.textContent = 'Sign out';
      await loadLocker();
      loginDialog.close();
      form.reset();
    } catch (error) {
      errorMessage.textContent = error.message;
    }
  });

  document.getElementById('verifyBtn').onclick = async () => {
    const documentId = document.getElementById('recordId').value.trim();
    const message = document.getElementById('verifyMsg');
    if (!documentId) {
      message.textContent = 'Please enter a Record ID.';
      return;
    }
    message.textContent = 'Checking the blockchain...';
    try {
      const result = await requestJson(`/api/verify/?document_id=${encodeURIComponent(documentId)}`);
      message.textContent = result.is_valid
        ? `✓ Record ${result.document_id} is verified on the blockchain.`
        : `Record ${result.document_id} could not be verified${result.error ? `: ${result.error}` : '.'}`;
    } catch (error) {
      message.textContent = error.message;
    }
  };

  const page = new URLSearchParams(window.location.search).get('page');
  const documentId = new URLSearchParams(window.location.search).get('document_id');
  if (page === 'verify') {
    document.querySelector('.nav button[data-page="verify"]').click();
    if (documentId) {
      document.getElementById('recordId').value = documentId;
      document.getElementById('verifyBtn').click();
    }
  }

  loadLocker().then(() => {
    signedIn = true;
    walletButton.textContent = 'Sign out';
  }).catch(error => {
    if (error.message !== 'Authentication is required.') {
      loginDialog.querySelector('.login-error').textContent = error.message;
    }
  });
})();
