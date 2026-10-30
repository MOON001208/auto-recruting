const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '../docs/index.html'), 'utf8');
const script = html.match(/<script defer>([\s\S]*?)<\/script>/)[1];
const cards = [];
const list = { innerHTML: '', appendChild: card => cards.push(card) };
const context = vm.createContext({
    URL, URLSearchParams, console,
    window: { addEventListener() {} },
    document: {
        addEventListener() {},
        getElementById: () => list,
        createElement: () => ({
            dataset: {},
            insertBefore(node) { this.jdInfo = node; },
            appendChild(node) { this.jdInfo = node; },
        }),
    },
});
vm.runInContext(script, context);
assert.equal(vm.runInContext(`getJobCategory({category: 'Data', hidden_keyword: '채용'})`, context), 'data');
assert.equal(vm.runInContext(`getJobCategory({hidden_keyword: 'MarTech'})`, context), 'data');
assert.equal(vm.runInContext(`getJobCategory({hidden_keyword: 'retail'})`, context), 'other');
assert.equal(vm.runInContext(`getJobCategory({hidden_keyword: '회계'})`, context), 'accounting');
vm.runInContext(`
    currentCategory = 'data';
    renderJobs([
        {title:'Low score', category:'Data', deadline:'', data_relevance:{score:0, jd_status:'unavailable'}},
        {title:'Higher score', category:'Data', deadline:'', data_relevance:{score:3, jd_status:'available', matched_keywords:['SQL','Python','dbt']}},
        {title:'HR posting', category:'HR', deadline:''}
    ]);
`, context);
assert.equal(cards.length, 2);
assert.match(cards[0].innerHTML, /Higher score/);
assert.match(cards[0].jdInfo.textContent, /SQL · Python · dbt/);
assert.match(cards[1].jdInfo.textContent, /JD 확인 필요/);
console.log('Dashboard category, JD ranking, and fallback display checks passed.');
