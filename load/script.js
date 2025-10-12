import http from 'k6/http';
import { SharedArray } from 'k6/data';
import { check, group, sleep } from 'k6';
import { exec, vu } from 'k6/execution';

const projects = new SharedArray('Projects', function(){
	return JSON.parse(open('./projects.json'));
});	

const users = new SharedArray('Users', function() {
	return JSON.parse(open('./users.json'));
});

export const options = {
  // A number specifying the number of VUs to run concurrently.
  vus: 5,
  // A string specifying the total duration of the test run.
  duration: '5s',

  // The following section contains configuration options for execution of this
  // test script in Grafana Cloud.
  //
  // See https://grafana.com/docs/grafana-cloud/k6/get-started/run-cloud-tests-from-the-cli/
  // to learn about authoring and running k6 test scripts in Grafana k6 Cloud.
  //
  // cloud: {
  //   // The ID of the project to which the test is assigned in the k6 Cloud UI.
  //   // By default tests are executed in default project.
  //   projectID: "",
  //   // The name of the test in the k6 Cloud UI.
  //   // Test runs with the same name will be grouped.
  //   name: "script.js"
  // },

  // Uncomment this section to enable the use of Browser API in your tests.
  //
  // See https://grafana.com/docs/k6/latest/using-k6-browser/running-browser-tests/ to learn more
  // about using Browser API in your test scripts.
  //
  // scenarios: {
  //   // The scenario name appears in the result summary, tags, and so on.
  //   // You can give the scenario any name, as long as each name in the script is unique.
  //   ui: {
  //     // Executor is a mandatory parameter for browser-based tests.
  //     // Shared iterations in this case tells k6 to reuse VUs to execute iterations.
  //     //
  //     // See https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/ for other executor types.
  //     executor: 'shared-iterations',
  //     options: {
  //       browser: {
  //         // This is a mandatory parameter that instructs k6 to launch and
  //         // connect to a chromium-based browser, and use it to run UI-based
  //         // tests.
  //         type: 'chromium',
  //       },
  //     },
  //   },
  // }
};

export function setup() {
	const token_req = http.post('http://localhost:8087/api/v1/token',
	{ username: 'admin@admin.fr', password: 'admin'});
	const token = token_req.json().access_token;

	for (const element of projects){
		const create_resp = http.post(
			'http://localhost:8087/api/v1/settings/projects',
			JSON.stringify(
				{ name: element}
			),
			{
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`},
			}
		);
		check(create_resp, {'status ok': (r) => r.status == 200 || r.status == 409});
		
	}
	for (const element of users){
		console.log(element);
		const create_user = http.post(
			'http://localhost:8087/api/v1/users',
			JSON.stringify(element),
			{
				headers: { 
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`},
			}
		);
		console.log(create_user.status);
		check(create_user, {'user created': (r) => r.status == 200 || r.status ==409});
		if(create_user.status == 409){
			const update_user = http.patch(
			'http://localhost:8087/api/v1/users',
			JSON.stringify(element),
			{
				headers: { 
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`},
			}
		);
		check( update_user, {'user updated': (r) => r.status == 200});
		}
	}
}
// The function that defines VU logic.
//
// See https://grafana.com/docs/k6/latest/examples/get-started-with-k6/ to learn more
// about authoring k6 scripts.
//
export default function() {
	// Log in
	let token;
	let project_to_use;
	let project_version;
	let current_user = users[vu.idInTest - 1];
	const user_projects = Object.keys(current_user.scopes);
	if (current_user.scopes['*'] == 'admin'){
		project_to_use = projects[Math.floor(Math.random() * projects.length)];
	}
	else{
		user_projects.splice(user_projects.indexOf('*'),1)
		project_to_use = user_projects[Math.floor(Math.random() * user_projects.length)];
	}
	console.log(vu.idInTest, project_to_use);
	
	group('Log in', function (){
		const token_req = http.post(
			'http://localhost:8087/api/v1/token',
			{
				username: current_user.username,
				password: current_user.password
			}
		);
		check(token_req, {'User login': (r) => r.status == 200});
		token = token_req.json().access_token;
	});
	
	group('Access project', function(){
		const accessProjReq = http.get(
			`http://localhost:8087/api/v1/projects/${project_to_use}`,
			{
				headers: {
					'Authorization': `Bearer ${token}`
				},
			}
		);
		check(accessProjReq, {'User access project': (r) => r.status == 200});
		
		
	});
	// List campaign
	// Record a bug
	// Log out
  const res = http.get('http://localhost:8087');
  check(res, {'status was 200': (r) => r.status == 200});
  
}
