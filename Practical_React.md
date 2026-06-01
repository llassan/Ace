top 50 mistakes/problems React developers commonly run into.

State Management
1. Storing derived state
const [filteredUsers, setFilteredUsers] = useState([]);

Instead derive it from existing state.

2. Mutating state directly
users.push(newUser);
setUsers(users);
3. Forgetting state updates are asynchronous
setCount(count + 1);
console.log(count); // old value
4. Multiple state updates using stale values
setCount(count + 1);
setCount(count + 1);
5. Using state when a ref is enough

Causes unnecessary re-renders.

6. Keeping too much state

Only store what's necessary.

7. Splitting tightly coupled state

Use useReducer when state transitions are related.

8. Deeply nested state structures

Makes updates painful and error-prone.

9. Not normalizing complex data

Leads to duplicate sources of truth.

10. Lifting state unnecessarily

Creates prop-drilling.

useEffect Problems
11. Missing dependency array
useEffect(() => {
  fetchData();
});

Runs every render.

12. Incorrect dependency array
useEffect(() => {
  fetchData(userId);
}, []);

Misses updates.

13. Stale closure problem
useEffect(() => {
  const id = setInterval(() => {
    setCount(count + 1);
  }, 1000);
}, []);

Use functional updates.

14. Infinite render loops
useEffect(() => {
  setData({});
}, [data]);
15. Using useEffect for derived state
useEffect(() => {
  setFullName(first + last);
}, [first, last]);
16. Forgetting cleanup
window.addEventListener(...)

Memory leaks.

17. Race conditions during fetches

Older requests may overwrite newer results.

18. Fetching data without aborting

Component unmounts before request completes.

19. Overusing useEffect

Many effects can be replaced by direct calculations.

20. Mixing unrelated concerns in one effect

Creates debugging nightmares.

Rendering Problems
21. Missing keys in lists
{items.map(item => <Item />)}
22. Using array index as key

Breaks when list changes order.

23. Creating expensive values on every render
const sorted = heavySort(data);
24. Rendering huge lists

Use virtualization.

25. Unnecessary parent re-renders

Affects entire subtree.

26. Unnecessary child re-renders

Use memoization when needed.

27. Inline object creation
<Component style={{ color: "red" }} />

New object every render.

28. Inline function creation everywhere
onClick={() => handleClick()}

Not always bad, but can break memoization.

29. Heavy computations inside JSX
30. Not understanding React reconciliation

Leads to unexpected remounting.

Hooks Mistakes
31. Calling hooks conditionally
if (user) {
  useEffect(...);
}
32. Calling hooks inside loops
33. Calling hooks inside nested functions
34. Wrong useMemo usage

Memoizing everything.

35. Wrong useCallback usage

Adding complexity without benefit.

36. Missing dependencies in useMemo

Produces stale values.

37. Missing dependencies in useCallback

Produces stale functions.

38. Using refs as state

UI won't update.

39. Overusing custom hooks

Makes debugging harder.

40. Violating Rules of Hooks

Top interview topic.

Data Fetching Problems
41. Fetching on every render
42. No loading state

Bad UX.

43. No error state

Application silently fails.

44. Duplicate API requests

Common in large apps.

45. Not caching responses

Libraries like React Query help.

Architecture & Performance
46. Prop drilling through many layers

Use Context carefully.

47. Putting everything in Context

Causes widespread re-renders.

48. Large components (1000+ lines)

Hard to maintain.

49. Not separating UI and business logic

Makes testing difficult.

50. Premature optimization

Adding memo, useMemo, and useCallback everywhere without measuring.

The 10 Most Important Interview Topics

If you're preparing for React interviews, focus heavily on:

Stale Closures
State vs Ref
useEffect Dependencies
React Reconciliation
Keys in Lists
Controlled vs Uncontrolled Components
Memoization (memo, useMemo, useCallback)
Context Re-render Problems
State Immutability
Custom Hooks & Rules of Hooks
