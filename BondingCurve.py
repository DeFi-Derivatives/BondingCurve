import smartpy as sp 

class ErrorMessages(sp.Contract): 

    def make(s):

        return ("Bonding_Curve_" + s)


    NotAdmin = make("Not_Admin")

    InsufficientXTZ = make("InsufficientXTZ")


class Library(ErrorMessages,sp.Contract): 

    def TransferFATwoTokens(sender,reciever,amount,tokenAddress,id):

        arg = [
            sp.record(
                from_ = sender,
                txs = [
                    sp.record(
                        to_         = reciever,
                        token_id    = id , 
                        amount      = amount 
                    )
                ]
            )
        ]

        transferHandle = sp.contract(
            sp.TList(sp.TRecord(from_=sp.TAddress, txs=sp.TList(sp.TRecord(amount=sp.TNat, to_=sp.TAddress, token_id=sp.TNat).layout(("to_", ("token_id", "amount")))))), 
            tokenAddress,
            entry_point='transfer').open_some()

        sp.transfer(arg, sp.mutez(0), transferHandle)


    def TransferFATokens(sender,reciever,amount,tokenAddress): 
       

        TransferParam = sp.record(
            from_ = sender, 
            to_ = reciever, 
            value = amount
        )

        transferHandle = sp.contract(
            sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))),
            tokenAddress,
            "transfer"
            ).open_some()

        sp.transfer(TransferParam, sp.mutez(0), transferHandle)

    def TransferToken(sender, reciver, amount, tokenAddress,id, faTwoFlag): 

        sp.if faTwoFlag: 

            Library.TransferFATwoTokens(sender, reciver, amount , tokenAddress, id )

        sp.else: 

            Library.TransferFATokens(sender, reciver, amount, tokenAddress)


class BondingCurve(Library):


    def __init__(self,_adminAddress,_governanceContract,_developerFundAddress):

        self.init(
            adminAddress = _adminAddress,
            governanceContract = _governanceContract,
            xtzDeposited = sp.nat(0),
            tokenDeposited = sp.nat(0),
            totalSupply = sp.nat(0),
            developerFundAddress = _developerFundAddress
        ) 


    # Transfer Delegation Rewards to Developer Address

    @sp.entry_point
    def default(self):
        
        # Transfering Delegation Amount for Research

        sp.send(self.data.developerFundAddress,sp.amount)


    @sp.entry_point
    def buyGovernanceToken(self,params):

        sp.set_type(params, sp.TRecord(
            recipient = sp.TAddress,
            tokenAmount = sp.TNat
        ))



        # Transfer Tokens 
        # Library.TransferToken(sp.sender, sp.self_address)

        # Mint Call

        mintParam = sp.record(
            address = params.recipient,
            value = params.tokenAmount
        )

        mintHandle = sp.contract(
            sp.TRecord(address = sp.TAddress, value = sp.TNat),
            self.data.governanceContract,
            "mint"
            ).open_some()

        sp.transfer(mintParam, sp.mutez(0), mintHandle)

    def buyXTZAmount(self,tokenAmount): 

        tokenSquare = sp.local('tokenSquare', self.data.totalSupply)

        tokenSquare.value *= tokenSquare.value 

        supplyAfterPurchase = sp.local('supplerAfterPurchase', self.data.totalSupply + tokenAmount)

        supplyAfterPurchase.value *= supplyAfterPurchase.value 

        xtzRequired = sp.local('xtzRequired', sp.nat(0))

        xtzRequired.value = sp.as_nat(supplyAfterPurchase.value - tokenSquare.value)

        xtzRequired.value = xtzRequired / 2 

        sp.verify(sp.utils.mutez_to_nat(sp.amount) >= xtzRequired.value, ErrorMessages.InsufficientXTZ)

        remainingBalance = sp.local('remainingBalance', sp.as_nat(sp.utils.mutez_to_nat(sp.amount) - xtzRequired.value))

        sp.if remainingBalance.value > 0: 

            sp.send(sp.sender, sp.nat_to_mutez(remainingBalance.value))


    def buyUsdAmount(self, tokenAmount):
        pass 



    @sp.entry_point
    def sellGovernanceToken(self,params):

        sp.set_type(
            params, sp.TRecord(
                recipent = sp.TAddress,
                tokenAmount = sp.TNat
            )
        )

        xtzAmount = sp.local('xtzAmount', sp.nat(0))
        tokenAmount = sp.local('tokenAmount',sp.nat(0))

        # Burn Call
        burnParam = sp.record(
            address = sp.sender,
            value = params.tokenAmount
        )

        burnHandle = sp.contract(
            sp.TRecord(address = sp.TAddress, value = sp.TNat),
            self.data.governanceContract,
            "burn"
            ).open_some()

        sp.transfer(burnParam, sp.mutez(0), burnHandle)

        # Transfer Tokens 

        # Library.TransferToken(sp.self_address, params.recipient, tokenAmount.value)


    @sp.entry_point
    def changeBaker(self,bakerAddress):

        sp.verify(sp.sender == self.data.adminAddress, ErrorMessages.NotAdmin)

        sp.set_delegate(bakerAddress)

    @sp.entry_point
    def changeDeveloperAddress(self,developerAddress): 

        sp.verify(sp.sender == self.data.adminAddress, ErrorMessages.NotAdmin)

        self.data.developerFundAddress = developerAddress


@sp.add_test(name = "Bonding Curve Contract")
def test(): 

    scenario = sp.test_scenario()
    
    # Deployment Accounts 
    adminAddress = sp.test_account("adminAddress")

    governanceTokenContract = sp.test_account("governanceTokenContract")

    developerAddress = sp.test_account("developerAddress")

    amm = BondingCurve(adminAddress.address, governanceTokenContract.address, developerAddress.address)
    scenario += amm 