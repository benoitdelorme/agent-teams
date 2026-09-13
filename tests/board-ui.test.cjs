const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function setup() {
  const html = fs.readFileSync(path.join(__dirname, '../tools/board/index.html'), 'utf8');
  // Test event handlers without starting the page's HTTP/SSE bootstrap.
  const script = html.match(/<script>([\s\S]*?)<\/script>/)[1]
    .replace(/^resync\(\)\.then\(connect\).*;$/m, '');
  const context = vm.createContext({
    document: {querySelector: () => ({addEventListener(){}}), querySelectorAll: () => []},
    window: {addEventListener(){}}, setInterval(){}, calls: []
  });
  vm.runInContext(script, context);
  vm.runInContext(`
    META.transitions = {doing: ['todo', 'qa'], qa: ['doing', 'done']};
    TASKS.set('T1', {id: 'T1', status: 'doing'});
    render = () => {};
    requestRender = () => {};
    toast = () => {};
    api = async (method, url, body) => { calls.push({method, url, body}); return {id:'T1', ...body}; };
  `, context);
  return context;
}

test('status choices use the server transition map', () => {
  const context = setup();
  assert.equal(vm.runInContext("canTransition('doing', 'backlog')", context), false);
  assert.equal(vm.runInContext("canTransition('doing', 'qa')", context), true);
  assert.match(vm.runInContext("statusOptions('doing')", context), /value="backlog" disabled/);
  vm.runInContext("META.transitions.doing = ['backlog']", context);
  assert.equal(vm.runInContext("canTransition('doing', 'backlog')", context), true);
});

test('dropping onto an invalid status sends no PATCH', async () => {
  const context = setup();
  await vm.runInContext(`
    drag = {id:'T1', over:'backlog', ghost:{remove(){}}, card:{classList:{remove(){}}}};
    endDrag();
  `, context);
  assert.equal(context.calls.length, 0);
  assert.equal(vm.runInContext("TASKS.get('T1').status", context), 'doing');
});

test('a permitted drop saves the status', async () => {
  const context = setup();
  await vm.runInContext(`
    drag = {id:'T1', over:'qa', ghost:{remove(){}}, card:{classList:{remove(){}}}};
    endDrag();
  `, context);
  assert.equal(context.calls.length, 1);
  assert.equal(context.calls[0].method, 'PATCH');
  assert.equal(context.calls[0].body.status, 'qa');
  assert.equal(vm.runInContext("TASKS.get('T1').status", context), 'qa');
});
