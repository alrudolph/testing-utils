Use PCB to know if a class was generated or not...

instead of all of the `@properties`

```
We can take

modles = [Model(name="company"), Model(name="member", requires=["company"])]

and convert to

```
RepoUtils {

    [company_id CompanyId] {
        company Company
    }

    [member_id MemberId] {
        member Member
    }

}
```

then

`repo_utils.with_company().with_member()`

will return

`RepoUtils_CopmanyMember`

and only have the `company` and `member` properties


```
