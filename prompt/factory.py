from product.models import Problem, Solution, Product
from django.shortcuts import get_object_or_404
from .models import Role


class PromptFactory:

    problems = []
    solutions = []

    def __init__(self, salesrep,outsourced_data,product,prompt) -> None:
        self.salesrep = get_object_or_404(Role,name=salesrep).name
        self.outsourced_data = outsourced_data
        self.product = product
        self.prompt = prompt
    

    def get_problems(self, data):
        for key in self.outsourced_data.keys():
            if key in data.get("checklist"):
                get_problems = Problem.objects.filter(
                    product=self.product,
                    **{"outsourced__{}__icontains".format(key): self.outsourced_data.get(key)}
                )
                if get_problems.exists():
                    self.problems.append([problem.name for problem in get_problems])
                all_problems = Problem.objects.all()
                self.problems.append([problem.name for problem in all_problems if all(val == "any" for val in problem.outsourced.values())])
        return self.problems

    def get_solutions(self):
        solutions = Solution.objects.filter(problem__name__in=self.prompt.data.get("confirmed_problems"))
        return self.solutions.append(solutions)

        