from django.db import models, connections
from django.shortcuts import get_object_or_404
from base.models import BaseModel
from product.models import Product, Company, Problem, Solution, GsheetSetting
from helpers.db.connection import connect_to_external_database
from helpers.gsheet.utils import execute_gsheet_formula
# Create your models here.

class Role(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self) -> str:
        return self.name

class ToneOfVoice(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self) -> str:
        return self.name


class Prompt(BaseModel):
    name = models.CharField(max_length=50)
    data = models.JSONField(default=dict)
    text_data = models.TextField(default='')
    tone_of_voice = models.ForeignKey(ToneOfVoice,on_delete=models.CASCADE, 
                                      null=True, blank=True)
    role = models.ForeignKey(Role,on_delete=models.CASCADE, 
                                      null=True, blank=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE, 
                                      null=True, blank=True)
    index = models.IntegerField(default=1)
    

    def __str__(self):
        return self.name
    
    @property
    def querying_info(self):
        queries = Query.objects.filter(prompt = self)
        querying_info = []
        for query_ in queries:
            company = get_object_or_404(Company, id = self.product.company.id)
            connect_to_external_database(company)
            with connections[company.name].cursor() as cursor:
                cursor.execute(query_.query)
                results = cursor.fetchall()
            
            query_data = {
                query_.name:results if results else query_.query
            }
            querying_info.append(query_data)

        return querying_info

    @property
    def get_problems(self):
        problems = Problem.objects.filter(product= self.product)
        sheet = GsheetSetting.objects.filter(company=self.product.company).last()
        problem_values = []
        if problems.exists():
            for problem in problems:
                problem_values.append({problem.name:execute_gsheet_formula(problem.gsheet_range,
                                                            problem.gsheet_formula,
                                                            spreadsheet_id=sheet.spreadsheet_id)})

        return problem_values

    @property
    def get_solutions(self):
        problems = Problem.objects.filter(product= self.product)
        sheet = GsheetSetting.objects.filter(company=self.product.company).last()

        solution_values = []
        for problem in problems:

            solutions = Solution.objects.filter(problem=problem)
            if solutions.exists():
                for solution in solutions:
                    solution_values.append({solution.name:execute_gsheet_formula(solution.gsheet_range,
                                                                solution.gsheet_formula,
                                                                spreadsheet_id=sheet.spreadsheet_id)})
        return solution_values


class Query(BaseModel):
    name = models.CharField(max_length=255)
    query = models.TextField()
    prompt = models.ForeignKey(Prompt,on_delete=models.CASCADE, 
                                      null=True, blank=True)
    
    def __str__(self) -> str:
        return self.name