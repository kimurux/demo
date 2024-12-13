let token = null;
let currentUser = null;

const loginForm = document.getElementById('loginForm');
const dashboard = document.getElementById('dashboard');
const newRequestForm = document.getElementById('newRequestForm');
const editRequestForm = document.getElementById('editRequestForm');
const adminPanel = document.getElementById('adminPanel');
const repairRequests = document.getElementById('repair-requests');
const userList = document.getElementById('userList');
const userInfo = document.getElementById('userInfo');

function showElement(element) {
    element.style.display = 'block';
}

function hideElement(element) {
    element.style.display = 'none';
}

function setToken(newToken) {
    token = newToken;
    localStorage.setItem('token', newToken);
}

function getToken() {
    return localStorage.getItem('token');
}

function clearToken() {
    token = null;
    localStorage.removeItem('token');
}

window.onload = function() {
    token = getToken();
    if (token) {
        getCurrentUser();
    }
};

function getCurrentUser() {
    fetch('http://localhost:8000/users/me', {
        headers: {
            'Authorization': 'Bearer ' + token
        }
    })
    .then(response => response.json())
    .then(user => {
        currentUser = user;
        showDashboard();
    })
    .catch(error => {
        console.log('Error:', error);
        showLoginForm();
    });
}

function showLoginForm() {
    hideElement(dashboard);
    hideElement(newRequestForm);
    hideElement(editRequestForm);
    hideElement(adminPanel);
    showElement(loginForm);
}

function showDashboard() {
    hideElement(loginForm);
    hideElement(newRequestForm);
    hideElement(editRequestForm);
    showElement(dashboard);
    userInfo.textContent = 'Logged in as: ' + currentUser.username + ' (Role: ' + currentUser.role + ')';
    console.log(currentUser.username+": "+currentUser.role);
    if (currentUser.role === 'admin') {
        showElement(adminPanel);
        getUsers();
        getRepairRequests();
    } else if (currentUser.role === "master") {
        getRepairRequests();
    } else {
        hideElement(adminPanel);
    }
}

document.getElementById('login-form').onsubmit = function(e) {
    e.preventDefault();
    let username = document.getElementById('username').value;
    let password = document.getElementById('password').value;

    fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'username=' + username + '&password=' + password,
    })
    .then(response => response.json())
    .then(data => {
        setToken(data.access_token);
        getCurrentUser();
    })
    .catch(error => {
        console.log('Login error:', error);
        alert('Login fail. Try again.');
    });
};

document.getElementById('logout-btn').onclick = function() {
    clearToken();
    currentUser = null;
    showLoginForm();
};

document.getElementById('new-request-btn').onclick = function() {
    hideElement(dashboard);
    showElement(newRequestForm);
};

document.getElementById('new-request-form').onsubmit = function(e) {
    e.preventDefault();
    let equipmentType = document.getElementById('equipment-type').value;
    let model = document.getElementById('model').value;
    let problemDescription = document.getElementById('problem-description').value;

    fetch('http://localhost:8000/repair-requests/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token,
        },
        body: JSON.stringify({equipment_type: equipmentType, model: model, problem_description: problemDescription}),
    })
    .then(response => response.json())
    .then(data => {
        alert('Request created');
        showDashboard();
    })
    .catch(error => {
        console.log('Error:', error);
        alert('Error create request');
    });
};

document.getElementById('edit-request-form').onsubmit = function(e) {
    e.preventDefault();
    let id = document.getElementById('edit-request-id').value;
    let equipmentType = document.getElementById('edit-title').value;
    let model = document.getElementById('edit-model').value;
    let problemDescription = document.getElementById('edit-description').value;
    let status = document.getElementById('edit-status').value;

    fetch('http://localhost:8000/repair-requests/', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token,
        },
        body: JSON.stringify({
            request_id: id,
            update_data: {equipment_type: equipmentType, model: model, problem_description: problemDescription, status: status}
        }),
    })
    .then(response => response.json())
    .then(data => {
        alert('Request updated');
        showDashboard();
    })
    .catch(error => {
        console.log('Error:', error);
        alert('Error update request');
    });
};

function getRepairRequests() {
    fetch('http://localhost:8000/repair-requests/', {
        headers: {
            'Authorization': 'Bearer ' + token,
        },
    })
    .then(response => response.json())
    .then(requests => {
        repairRequests.innerHTML = '';
        for (let request of requests) {
            let div = document.createElement('div');
            div.innerHTML = '<h3>' + request.equipment_type + ' (' + request.model + ')</h3>' +
                            '<p>Problem: ' + request.problem_description + '</p>' +
                            '<p>Status: ' + request.status + '</p>';
            
            if (currentUser.role === 'admin' || currentUser.role === 'master') {
                let editBtn = document.createElement('button');
                editBtn.textContent = 'Edit';
                editBtn.className = 'edit-btn';
                editBtn.onclick = function() { showEditForm(request); };
                div.appendChild(editBtn);
            }

            if (currentUser.role === 'admin') {
                let deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Delete';
                deleteBtn.className = 'delete-btn';
                deleteBtn.onclick = function() { deleteRequest(request.id); };
                div.appendChild(deleteBtn);
            }

            if (currentUser.role === 'master' && request.status === 'NEW') {
                let assignBtn = document.createElement('button');
                assignBtn.textContent = 'Assign to me';
                assignBtn.className = 'assign-btn';
                assignBtn.onclick = function() { assignRequest(request.id); };
                div.appendChild(assignBtn);
            }

            repairRequests.appendChild(div);
        }
    })
    .catch(error => {
        console.log('Error:', error);
    });
}

function showEditForm(request) {
    document.getElementById('edit-request-id').value = request.id;
    document.getElementById('edit-title').value = request.equipment_type; // Используем тип оборудования
    document.getElementById('edit-description').value = request.problem_description; // Описание проблемы
    document.getElementById('edit-status').value = request.status; // Статус
    hideElement(dashboard);
    showElement(editRequestForm);
}

function deleteRequest(id) {
    if (confirm('Вы действительно хотите удалить?')) {
        fetch('http://localhost:8000/repair-requests/', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token,
            },
            body: JSON.stringify({request_id: id}),
        })
        .then(response => response.json())
        .then(data => {
            alert('Запрос удалён');
            getRepairRequests();
        })
        .catch(error => {
            console.log('Error:', error);
            alert('Ошибка удаления');
        });
    }
}

function assignRequest(id) {
    fetch('http://localhost:8000/repair-requests/', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token,
        },
        body: JSON.stringify({
            request_id: id,
            update_data: {master_id: currentUser.id, status: 'IN_PROGRESS'} // Статус обновляется на "в процессе ремонта"
        }),
    })
    .then(response => response.json())
    .then(data => {
        alert('Request assigned to you');
        getRepairRequests();
    })
    .catch(error => {
        console.log('Error:', error);
        alert('Error assign request');
    });
}

function getUsers() {
    fetch('http://localhost:8000/users/', {
        headers: {
            'Authorization': 'Bearer ' + token,
        },
    })
    .then(response => response.json())
    .then(users => {
        userList.innerHTML = '';
        for (let user of users) {
            let div = document.createElement('div');
            div.innerHTML = '<p>Username: ' + user.username + ', Role: ' + user.role + ', Full Name: ' + user.full_name + ', Phone: ' + user.phone + '</p>';
            
            let deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete User';
            deleteBtn.className = 'delete-btn';
            deleteBtn.onclick = function() { deleteUser(user.id); };
            div.appendChild(deleteBtn);

            userList.appendChild(div);
        }
    })
    .catch(error => {
        console.log('Error:', error);
    });
}

function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user?')) {
        fetch('http://localhost:8000/users/', {
            method: 'DELETE',
            headers: {
                'Authorization': 'Bearer ' + token,
            },
            body: JSON.stringify({id: userId}),
        })
        .then(response => response.json())
        .then(data => {
            alert('User deleted');
            console.log(userId+" are deleted")
        })
        .catch(error => {
            console.log('Error:', error);
            alert('Error delete user');
        });
    }
}
