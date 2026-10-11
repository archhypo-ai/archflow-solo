# Bring the Specialist

## AKA Involve the Right People, Participation Recommendations

Some uncertainties that arise in software development, which can be related to the project domain or a specific technology, might require some specific expertise to be handled. The lack of this expertise in the team might bring uncertainty to the project. The involvement of individuals with specialized expertise is particularly beneficial in this case, as they bring essential knowledge that can help to reduce this uncertainty. Without a professional with the required expertise, the team should resort to research and other strategies to obtain the required knowledge, which could be time consuming. These specialized professionals usually do not have much availability and are considered a resource that should be used wisely.

**How to reduce uncertainty that comes from the team's lack of knowledge on a given domain or technology?**

- A technology expert who has employed a specific solution or component is in a better position to explain the trade-offs of using the solution.
- Domain experts might have access to resources that can bring helpful information to handle uncertainty.
- Domain and technology experts might not be directly accessible to the team without an explicit directive or external interference.
- The lack of an expert might require team members to research and experiment, which can consume time and have a high cost.
- Some problems and solutions related to a given uncertainty might only be perceived by an expert in the field.
- Assigning team members to activities that do not align with their expertise can lead to additional effort.

Therefore:

**Identify the knowledge needed for a given uncertainty and involve individuals with the right skills or knowledge in activities where this expertise can reduce the uncertainty.**

The first step involved is to establish the type of knowledge that might help to handle the uncertainty. The next stage focuses on considering the availability of professionals with the required specific expertise. This evaluation also holds when the knowledge is from any team member, a potential expert in the company, or other external specialists. This step assesses their availability regarding time, existing workload, and other obligations.

Then, the next activity is to evaluate the viability and cost of involving them in addressing the uncertainty. This step aims to balance the benefits of their expertise against the disadvantages, ensuring that its acquisition is viable and relevant regarding certain project limitations. In some cases, other changes in the process might be needed to enable expert participation.

Once the viability is established, teams need to identify the appropriate activities within the software development lifecycle where the expertise of the identified professionals would have the most significant impact. This could include various activities, such as requirements analysis, design, testing, or strategic planning.

In cases where there is a lack of available experts, the team might consider alternatives. One of the actions can be to explore the specialization of existing team members in the required knowledge domain. This could involve implementing training programs, architectural spikes, or tracer bullets to build expertise within the team.

## Consequences

The following are the consequences of using this pattern:

- Involvement of experts reduces uncertainties in project activities. Their knowledge helps minimize the chances of errors or delays.
- Expertise might reduce the time of the problem-solving process.
- An expert might identify problems and solutions that would be neglected.
- The interaction of the expert with the team might result in knowledge transfer.
- Depending on the availability of experts, resource constraints may emerge. Limited access to specialized individuals can restrict the resolution of the uncertainty, potentially impacting project timelines.
- Involving external experts or specialists might incur additional costs.
- It may create the need for additional preliminary planning before implementing this guideline, as well as earning support from the team.
- One potential challenge is that too much dependence on an individual specialist may arise in a project and may be complicated when a specialist is out of the team or the project.
- When there is no expert available, an alternative is to build the required knowledge and skill in the team members; however, that alternative might only reduce uncertainty in the long term.

## Related Patterns

The pattern **Gathering Experts** can be used to plan the participation of the experts in the required activities. If a given expertise is very important for the project as a whole, **Domain Expertise In Roles** can be used to make sure that someone with that knowledge will be available to the team.

## Examples

_As an example, in the context of developing an insurance system, a critical uncertainty related to reliability emerges regarding whether the rules implemented in the software match the ones in the insurance contract and legislation. To reduce this uncertainty, a solution involves using this pattern to suggest the participation of an insurance analyst in the requirements specification when they involve this kind of rule. An additional guideline could also suggest its participation in defining more realistic test cases (which the expert can do directly if the team decides to use a Behavior-Driven Development approach). The uncertainty is reduced because his broader knowledge in this complex field prevents some specific cases from being neglected. The adoption of Bring the Specialist in this case can have a high impact on the reliability._
