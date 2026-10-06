const allLessons = [
  { number: 1, slug: 'solow', title: 'The Solow model', short: 'Growth & convergence', question: 'What determines where capital settles?', description: 'Saving, diminishing returns and the journey to a steady state.', topic: 'Growth', source: 'Tutorial_1.py' },
  { number: 2, slug: 'household', title: 'Consumption over time', short: 'Consumption & wealth', question: 'How much can a household afford to consume?', description: 'Wealth paths, consumption choices and the terminal condition.', topic: 'Continuous time', source: 'Tutorial_2.py' },
  { number: 3, slug: 'saddle-path', title: 'Finding the saddle path', short: 'The saddle path', question: 'Which initial choice leads to equilibrium?', description: 'A phase diagram and a shooting algorithm, one guess at a time.', topic: 'Continuous time', source: 'Tutorial_3.py' },
  { number: 6, slug: 'bellman', title: 'Thinking recursively', short: 'The Bellman equation', question: 'How does tomorrow change today’s decision?', description: 'Build a value function through small, visible Bellman updates.', topic: 'Dynamic programming', source: 'Problem_Set_3_Q3.py' },
  { number: 7, slug: 'extraction', title: 'A stock, a price, a choice', short: 'Resource extraction', question: 'Does a bigger stock change the extraction fraction?', description: 'Homogeneity, stochastic prices and the cost of capacity.', topic: 'Dynamic programming', source: 'Problem_Set_4_Q2.py' },
  { number: 9, slug: 'investment', title: 'When doing nothing is optimal', short: 'Lumpy investment', question: 'Why do firms wait before investing?', description: 'Fixed costs, resale losses and the region of inaction.', topic: 'Firm dynamics', source: 'Problem_Set_5_Q3.py' },
  { number: 10, slug: 'rbc', title: 'How local is a local approximation?', short: 'RBC & approximation', question: 'When do two decision rules stop agreeing?', description: 'Numerical and log-linear RBC policies facing the same shock.', topic: 'Business cycles', source: 'Problem_Set_4_Q4.py' }
];

// Keep the remaining lessons in the source tree while exposing only the
// currently active model on the website.
export const lessons = allLessons.filter(lesson => lesson.slug === 'solow');

export function withBase(path = '') {
  return `${import.meta.env.BASE_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
}
